import argparse
from datetime import datetime
import pandas as pd

def process(path):
    df = pd.read_json(path)
    df = df.sort_values(by='timestamp')

    df_edited = df.copy()
    selector = None

    


    while(selector != 6):
        try:
            print("File loaded, please choose how to display your data:")
            print("1) Search by time: from XX to XX")
            print("2) Search by user")
            print("3) Search by log code")
            print("4) Return to normal")
            print("5) Dump data to JSON")
            print("6) Exit")
            

            selector = int(input("Select: "))
        except ValueError:
            print("That's not a valid integer!")

        match selector:
            case 1:
                time_str = input("Enter time (YYYY-MM-DD HH:MM:SS): ")

                error_flag = True
                while (error_flag):
                    try:
                        time_mark = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        error_flag = False
                    except ValueError:
                        print("Try again")
                        time_str = input("Enter time (YYYY-MM-DD HH:MM:SS): ")

                df_edited = df_edited[df_edited['timestamp'] > time_mark].reset_index(drop=True)

            case 2:
                username = input("Enter username: ")

                mask = df_edited['author'].isin([username])
                if mask.any():
                    df_edited = df_edited[mask]
                else:
                    print("No such user in logs")

            case 3:
                error_flag = True
                while (error_flag):
                    try:
                        code = int(input("Enter code number: "))
                        error_flag = False
                    except ValueError:
                        print("Try again")
                mask = df_edited['code'].isin([code])
                if mask.any():
                    df_edited = df_edited[mask]
                else:
                    print("No such code in logs")

            case 4:
                df_edited = df.copy()
            case 5:
                df_edited.to_json(f"{datetime.now().strftime('%H:%M:%S')}.json", 
                                  indent=4, orient='records', date_format='iso')
                print("Dump succesful")
            case 6:
                print("Program shutdown initiated")

        print(df_edited)
                




                


                


    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path",
                            nargs="?",
                            type=str,
                            const = "../logs/logs.json",
                            default = "../logs/logs.json",
                            help="Relative path to logs, default: ../logs/logs.json")
    args = parser.parse_args()
    process(args.path)

if __name__ == '__main__':
    main()