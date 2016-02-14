import sqlite3
import requests
from lxml import etree
import os

import parl_init_TWFY as pi_TWFY
import parl_init_GOV as pi_GOV

def create_database(dbname='parl.db'):
    if os.path.isfile(dbname):
        os.remove(dbname)
    with sqlite3.connect(dbname) as connection:
        cur = connection.cursor()
        cur.execute("CREATE TABLE MPCommons (Name Text, Constituency Text, MP Boolean,\
                                            Party Text, ImageUrl Text, MemberId Number,\
                                            PersonId Number, OfficialId Number)")
        cur.execute("CREATE TABLE Offices  (PersonId Number, Office Text,\
                                            StartDate Text, EndDate Text, Name Text, Title Text)")
        cur.execute("CREATE TABLE Addresses (OfficialId Number, AddressType Text, Address Text)")

def setup_archipelago():
    try:
        create_database()
        pi_TWFY.TWFY_setup()
        pi_GOV.GOV_setup()
    except: #bad
        if os.path.isfile('parl.db'):
            os.remove('parl.db')
            raise

def is_arch_setup():
    return os.path.isfile('parl.db') 


if __name__ == '__main__':
    if not is_arch_setup():
        setup_archipelago()
