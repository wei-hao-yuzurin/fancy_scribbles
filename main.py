from contextlib import asynccontextmanager
from datetime import datetime, date, time, timedelta
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from jose import JWTError, jwt
import os

from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from typing import Optional, List

from sqlalchemy import create_engine, or_, Column, Integer, String, Date, ForeignKey, Table, text, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session, joinedload
from sqlalchemy.exc import OperationalError

import time
from typing import Optional, List

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24

def create_db_engine():
    for attempt in range(10):
        try:
            eng = create_engine(DATABASE_URL)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng
        except OperationalError:
            time.sleep(2)
    raise Exception("Could not connect to database")

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_tables():
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(lifespan=lifespan)



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    notes = relationship("NoteDB", back_populates="owner", cascade="all, delete-orphan")


class TagDB(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    notes = relationship("NoteDB", secondary="note_tags", back_populates='tags')

class NoteDB(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default=f'Заметка {id}')
    text = Column(String)
    created_at = Column(Date)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("UserDB", back_populates="notes")
    tags = relationship("TagDB", secondary = "note_tags", back_populates="notes")

note_tags = Table(
    'note_tags', Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)



# Base.metadata.create_all(bind=engine)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
) 

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str



def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_tokens(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserDB:
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user=db.query(UserDB).filter(UserDB.email == email).first()
    if user is None:
        raise credentials_exception
    return user




class Note(BaseModel):
    id: int | None = None
    title: str = "Заметка"
    text: str
    tags: List[str] = []
    created_at : date = None

    class Config:
        from_attributes=True

def get_or_create_tag(db: Session, tag_name=str):
    tag=db.query(TagDB).filter(TagDB.name==tag_name).first()
    if not tag:
        tag = TagDB(name=tag_name)
        db.add(tag)
        db.flush()
    return tag

def note_db_to_pydantic(note_db: NoteDB) -> Note:
    return Note(
        id=note_db.id,
        title=note_db.title,
        text=note_db.text,
        tags = [tag.name for tag in note_db.tags],
        created_at=note_db.created_at
    )

notes = []

@app.get("/api/notes")
def get_notes(search: Optional[str] = None,
              tag: Optional[str]= None,
              start_date: Optional[date]=None,
              end_date: Optional[date]=None,
              db: Session = Depends(get_db),
              current_user: UserDB = Depends(get_current_user),
              page: int = 1,
              limit: int = 5,
              ):
    
    query = db.query(NoteDB).filter(NoteDB.owner_id == current_user.id)
        
    if search:
        search_lower = f"%{search.lower()}%"
        query = query.filter((NoteDB.title.ilike(search_lower)) | (NoteDB.text.ilike(search_lower)))
        
    if tag:
        query = query.join(NoteDB.tags).filter(TagDB.name == tag)
        
    if start_date: query = query.filter(NoteDB.created_at >= start_date)
    if end_date: query = query.filter(NoteDB.created_at <= end_date)

    total = query.count()
    total_pages = (total + limit - 1) // limit

    offset = (page - 1) * limit

    notes_db = (
        query
        .order_by(NoteDB.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for n in notes_db:
        results.append(Note(
            id=n.id, title=n.title, text=n.text, 
            tags=[t.name for t in n.tags], created_at=n.created_at
        ))
    return {
    "items": results,
    "page": page,
    "limit": limit,
    "total": total,
    "total_pages": total_pages
    }

@app.get("/api/notes/{note_id}", response_model=Note)
def get_note_by_id(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    note_db = (
        db.query(NoteDB)
        .options(joinedload(NoteDB.tags))
        .filter(
            NoteDB.id == note_id,
            NoteDB.owner_id == current_user.id
        )
        .first()
    )

    if not note_db:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    return note_db_to_pydantic(note_db)


@app.post("/api/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password)
    db_user = UserDB(email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_tokens(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/notes", response_model=Note)
def create_note(
    note: Note, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    db_note = NoteDB(
        title=note.title, 
        text=note.text, 
        created_at=date.today(),
        owner_id=current_user.id
    )
    
    for tag_name in note.tags:
        db_note.tags.append(get_or_create_tag(db, tag_name))
        
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    return Note(
        id=db_note.id, title=db_note.title, text=db_note.text,
        tags=[t.name for t in db_note.tags], created_at=db_note.created_at
    )

@app.put("/api/notes/{note_id}", response_model=Note)
def update_note(
    note_id: int, 
    updated_note: Note, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user) # <--- PROTECTED
):
    note_db = db.query(NoteDB).filter(NoteDB.id == note_id, NoteDB.owner_id == current_user.id).first()
    if not note_db:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    
    note_db.title = updated_note.title
    note_db.text = updated_note.text
    
    note_db.tags.clear()
    for tag_name in updated_note.tags:
        note_db.tags.append(get_or_create_tag(db, tag_name))
        
    db.commit()
    db.refresh(note_db)
    
    return Note(
        id=note_db.id, title=note_db.title, text=note_db.text,
        tags=[t.name for t in note_db.tags], created_at=note_db.created_at
    )


@app.delete("/api/notes/{note_id}")
def delete_note(
    note_id: int, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user) # <--- PROTECTED
):
    note_db = db.query(NoteDB).filter(NoteDB.id == note_id, NoteDB.owner_id == current_user.id).first()
    if not note_db:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    
    db.delete(note_db)
    db.commit()
    return {"message": "Note deleted successfully"}