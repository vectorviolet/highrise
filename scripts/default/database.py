#-# Import Packages #-#
import sqlite3
import sys
import os

#-# Database Class #-#
class Database():

    def __init__(self, name):

        self.name = name
    
    def Connect(self) -> bool:
        
        try:

            # Check if there is no databases folder
            if not os.path.exists("databases"):
                os.makedirs("databases")
                print("==> Created databases folder!")
        
            self.connection = sqlite3.connect(("databases/" + self.name + ".db")) 

        except Exception as error:
            
            print("==> Failed to connect to database!", error)

            return False
        
        else:

            return True
        
    def GetCursor(self):

        return self.connection.cursor()
    
    def Execute(self, sql):
        
        try:
            
            return self.GetCursor().execute(sql)
            
        except Exception as error:

            print("An error occured during execute sql code:", error)
            
            return sys.exit()

    def Commit(self):

        self.connection.commit()

    def Disconnect(self):

        self.connection.close()