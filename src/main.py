from tkinter import Tk
from calendar_app import CalendarApp

def main():
    root = Tk()
    root.title("Semester Calendar")
    app = CalendarApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()