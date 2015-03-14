#create all required databases (if not existent)
#populate the databases with information drawn from TWFY API
import sqlite3
import requests
from lxml import etree
import os
import TWFY_key  #a file; only contains:  key = 'your_key_string'


##############
key = TWFY_key.key
output = 'xml'
site= 'http://www.theyworkforyou.com/'
base = 'api/%s?key=%s&output=%s' % ('%s', key, output)
##############

def create_database():
    if os.path.isfile('parl.db'):
        os.remove('parl.db')
    with sqlite3.connect('parl.db') as connection:
        cur = connection.cursor()
        cur.execute("CREATE TABLE MPCommons (Name Text, Constituency Text, MP Boolean,\
                                            Party Text, ImageUrl Text, MemberId Number,\
                                            PersonId Number)")
        cur.execute("CREATE TABLE Offices  (PersonId Number, Office Text,\
                                            StartDate Text, EndDate Text, Name Text)")

def fetch_xml_online(base_arg, bonus_arg=''):
    url = site + base%base_arg + bonus_arg
    
    data_request = requests.get(url)
    data_req_string = data_request.content
    data_xml = etree.fromstring(data_req_string)

    return data_xml

def load_constituencies():
    constit_xml = fetch_xml_online('getConstituencies')
    constituencies = []

    for c in constit_xml.findall('match'):
        constituencies.append((c.find('name').text,)) #tuple for 'executemany' statement
    
    with sqlite3.connect('parl.db') as connection:
        cur = connection.cursor()
        cur.execute('DELETE from MPCommons')
        cur.executemany("INSERT INTO MPCommons \
                        VALUES(null,?, 0, null,null,0,0)", constituencies)
        connection.commit()

def return_mp_and_office_details_from_xml(mp_xml):
    mps_list = []
    offices_list = []

    name_xml = mp_xml.find('name')
    if name_xml is None:
        name_xml = mp_xml.find('full_name')

    #for mp in mps_xml.findall('match'):
    mps_list.append((
                    name_xml.text, 
                    mp_xml.find('party').text,
                    int(mp_xml.find('member_id').text),
                    int(mp_xml.find('person_id').text),
                    mp_xml.find('constituency').text,
                    ))

    
    if mp_xml.find('office') is not None:
        jobs = mp_xml.find('office')
        for job in jobs.findall('match'):
            title = job.find('position').text
            if title == None:
                title = job.find('dept').text
                
            offices_list.append((
                                int(mp_xml.find('person_id').text),
                                title,
                                job.find('from_date').text,
                                job.find('to_date').text,
                                name_xml.text,
                                ))
    return (mps_list, offices_list)

def load_details_from_major_parties_mps():
    mps_list = []
    offices_list = []
    parties = ['conservative', 'labour', 'liberal democrat', 'green', 'independent', 'ukip',
                    'DUP', 'sinn fein', 'sdlp', 'plaid cymru', 'scottish national party']
    
    for party in parties:
        mps_xml = fetch_xml_online('getMPs', '&party=%s'%party)
        for mp_xml in mps_xml.findall('match'):
            party_mps, party_offices = return_mp_and_office_details_from_xml(mp_xml)
            mps_list.extend(party_mps)
            offices_list.extend(party_offices)
            
    with sqlite3.connect('parl.db') as connection:
        cur = connection.cursor()
        cur.executemany('UPDATE MPCommons SET Name=?,Party=?,MP=1,MemberId=?,PersonId=?\
                        WHERE Constituency=?', mps_list)
        cur.executemany('INSERT INTO Offices VALUES(?,?,?,?,?)', offices_list)
        connection.commit()

def load_straggler_mp_details():
    with sqlite3.connect('parl.db') as connection:
        cur = connection.cursor()
        cur.execute('SELECT Constituency FROM MPCommons WHERE MP=0')

        empty_seats = cur.fetchall()

        for seat in empty_seats:
            seat_xml = fetch_xml_online('getMP', '&constituency=%s'%seat)
            print etree.tostring(seat_xml)
            mp, office = return_mp_and_office_details_from_xml(seat_xml)
            print mp, office
            
            '''if seat_xml.find('error') is None:
                mp_id = int(seat_xml.find('member_id').text)
                name = seat_xml.find('first_name').text+' '+seat_xml.find('last_name').text
                party = seat_xml.find('party').text
                person_id = int(seat_xml.find('person_id').text)
            else:
                mp_id = 0
                name = 'Empty Seat'
                party = 'Empty Seat'
                person_id = 0
            constituency = seat_xml.find('constituency').text

            straggler = (name, party, mp_id, person_id, constituency)'''
            cur.executemany('UPDATE MPCommons SET Name=?,Party=?,MP=1,MemberId=?,PersonId=?\
                       WHERE Constituency=?', mp)
        connection.commit()

def download_images_from_person_id(person_id):
    image_req = requests.get(site+'images/mps/%d.jpg'%person_id)
    with open('profile_images/%d.jpg'%person_id, 'w') as img:
        img.write(image_req.content)
        img.close()

def load_images_for_imageless_mps():
    if not os.path.exists('profile_images'):
        os.makedirs('profile_images')
    with sqlite3.connect('parl.db') as connection:
        cur = connection.cursor()
        cur.execute('SELECT PersonId FROM MPCommons WHERE ImageUrl IS NULL')
        
        mps_missing_images = cur.fetchall()
        for mp_tuple in mps_missing_images:
            person_id = mp_tuple[0]
            download_images_from_person_id(person_id)
            cur.execute('UPDATE MPCommons SET ImageUrl=? WHERE PersonId=?',
                           ('images/mps/%s.jpg'%person_id, person_id))
            connection.commit()




def initial_setup():
    create_database()
    load_constituencies()
    load_details_from_major_parties_mps
    load_straggler_mp_details()
    load_images_for_imageless_mps()

if __name__ == '__main__':
    create_database()
    print'hey'
    load_constituencies()
    print'yo'
    load_details_from_major_parties_mps()

    load_straggler_mp_details()
    #load_images_for_imageless_mps()



