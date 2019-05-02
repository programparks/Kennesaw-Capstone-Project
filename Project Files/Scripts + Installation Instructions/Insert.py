import json
import pyodbc
import glob
import sys
from Crawler import login

import sys
# from urllib import unquote
from urllib import parse

import requests
import re
from lxml import etree

from bs4 import BeautifulSoup

import os, json, time

from Crawler import crawl

userName = 'zdowning@students.kennesaw.edu  '
passWD = 'password1234'


server = 'itcapstone.database.windows.net'

cnxn = pyodbc.connect('Driver={SQL Server};Server=tcp:itcapstone.database.windows.net,1433;Database=CAPSTONE;Uid=capstone@itcapstone;Pwd=Alumnidatabase!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
cursor = cnxn.cursor()
alumni_first = ""
alumni_last = ""
alumni_school = ""
alumni_program = ""
alumni_degree = ""
alumni_graduation = ""

class Alumni:
    first_name = ""
    last_name = ""
    school_name = ""
    id = ""
    degree = ""
    graduation_date = ""
    linked_in = ""
    location = ""
    job_title = ""
    start_date = ""
    end_date = ""
    alumni_education = []
    job_history = []
    skill_list = []

    def __init__(self,first,last,id,linked_in,education_list,job_history,skill_list):
        self.first_name = first
        self.last_name = last
        self.id = id
        self.linked_in = linked_in
        self.alumni_education = education_list
        self.job_history = job_history
        self.skill_list = skill_list

class Education:
    degree = ""
    fieldOfStudy = ""
    school_name = ""
    graduation_date = ""

    def __init__(self, degree,field,schoolName,graduation_date):
        self.degree = degree
        self.fieldOfStudy = field
        self.school_name = schoolName
        self.graduation_date = graduation_date.strip()

class Job:
    title = ""
    company = "",
    startDate = "",
    endDate = "",

    def __init__(self,title,company,startDate,endDate):
        self.title = title
        self.company = company
        self.startDate = startDate.strip()
        self.endDate = endDate.strip()

#Reads from search_strings.txt to fine one student
def insert_one():
    s = login(userName,passWD)
    search_file = open('search_strings.txt', 'r', encoding='UTF8')
    for line in search_file:
        keywords = []
        keywords = line.split(",")
        global alumni_first
        alumni_first = keywords[0]
        global alumni_last
        alumni_last = keywords[1]
        global alumni_school
        alumni_school = keywords[2]
        global alumni_program
        alumni_program = keywords[3]
        global alumni_degree
        alumni_degree = keywords[4]
        print(alumni_first)
        search_string = alumni_first + " " + alumni_last + " "+  alumni_school + " " + \
                            alumni_program + " "
        crawl(s,search_string,"one")
        Insert("one")

#Takes user input to search for multiple students
def insert_many():
    s = login(userName, passWD)
    global alumni_school
    alumni_school = input("Enter the University's name: ")
    global alumni_program
    alumni_program = input("Enter the program name: ")
    global alumni_degree
    alumni_degree = input("Enter the degree type (BS, MS, etc.): ")
    global alumni_graduation
    alumni_graduation = input("Enter the graduation year: ")
    search_string = alumni_degree + " " + alumni_program + " " + alumni_school + " " + " " + \
                    alumni_graduation
    print(search_string)
    crawl(s,search_string,"many")
    Insert("many")

#Check if duplicate education was returned from JSON
def is_education_duplicate(education_object, education_list = []):
    for i in range(0,len(education_list)):
        if (education_object.degree == education_list[i].degree) and \
            (education_object.fieldOfStudy == education_list[i].fieldOfStudy) and \
            (education_object.school_name == education_list[i].school_name) and \
            (education_object.graduation_date == education_list[i].graduation_date):
            return True
    return False

#Check if it's the alumni we're looking for
def doesSearchMatch(alumni,num):
    education_list = alumni.alumni_education
    if num == "one":
        if (alumni_first.strip() in alumni.first_name.strip()) and (alumni_last.strip() in alumni.last_name):
            for i in range(0,len(education_list)):
                print(alumni_degree[0])
                degree_stripped = education_list[i].degree.strip().lower()
                alumni_degree_stripped = alumni_degree.strip().lower()
                if len(degree_stripped) > 0:
                    if (alumni_program.strip() in education_list[i].fieldOfStudy) and (alumni_school.strip() in education_list[i].school_name) and \
                        (degree_stripped[0] == alumni_degree_stripped[0]):
                        return True
    if num == "many":
        for i in range(0, len(education_list)):
            degree_stripped = education_list[i].degree.strip().lower()
            alumni_degree_stripped = alumni_degree.strip().lower()
            if len(degree_stripped) > 0:
                if (alumni_program.strip() in education_list[i].fieldOfStudy) and (
                        alumni_school.strip() in education_list[i].school_name) and \
                        (degree_stripped[0] == alumni_degree_stripped[0]):
                    return True
    return False

#Check if a duplicate job was returned from JSON
def is_job_duplicate(job_object, job_list = []):
    for i in range(0,len(job_list)):
        if (job_object.company == job_list[i].company) and \
           (job_object.endDate == job_list[i].endDate) and \
           (job_object.startDate == job_list[i].startDate) and \
           (job_object.title == job_list[i].title):
            return True
    return False


#Check if a duplicate skill was returned from JSON
def is_skill_duplicate(skill_object,skill_list = []):
    for i in range(0, len(skill_list)):
        if skill_object == skill_list[i]:
            return True
    return False

#Insert into database from JSON
def Insert(num):
    AlumniList = []
    #Get alumni information for every file
    for filename in glob.glob('people_info\*json.txt'):
        education_list = []
        job_list = []
        skill_list = []
        with open(filename.title()) as json_file:
            data = json.load(json_file)
            for fName in data['nameUrlId']:
                first_name = fName['firstName']
            for lName in data['nameUrlId']:
                last_name = lName['lastName']
            for alumniId in data['nameUrlId']:
                id = alumniId['id']
            for url in data['nameUrlId']:
                linked_in = url['linkedInUrl']
            for education in data['education']:
                degree = education['degree']
                field = education['field']
                schoolName = education['schoolName']
                graduation_date = education['endDate']
                education_object = Education(degree,field,schoolName,graduation_date)
                duplicate = is_education_duplicate(education_object,education_list)
                if duplicate != True:
                    education_list.append(education_object)
            for position in data['jobHistory']:
                title = position['title']
                company = position['company']
                startDate = position['startDate']
                endDate = position['endDate']
                job_object = Job(title,company,startDate,endDate)
                duplicate = is_job_duplicate(job_object,job_list)
                if duplicate != True:
                    job_list.append(job_object)
            for skill in data['skills']:
                skill_name = skill['skill']
                duplicate = is_skill_duplicate(skill_name,skill_list)
                if duplicate != True:
                    skill_list.append(skill_name)
            json_file.close()
            os.remove(filename)
        AlumniList.append(Alumni(first_name,last_name,id,linked_in,education_list,job_list,skill_list))

    for alumni in AlumniList:
        #Does the search match what we're looking for?
        search_matches = doesSearchMatch(alumni,num)
        if search_matches == True:
            print(alumni_first + " " + alumni_last + " " + alumni_school)
            print("Does the search match? " + str(search_matches))
            try:#
                cursor.execute("Insert Into dbo.Alumni(alumni_id,first_name,last_name,linkedid_link,school,education_name,degree) " +
                               "Values(" + "\'" + alumni.id + "\'" + ","
                                           "\'" + alumni.first_name + "\'" + ","
                                           "\'" + alumni.last_name + "\'" + ","
                                           "\'" + alumni.linked_in + "\'" + ","
                                           "\'" + alumni_school + "\'" + "," 
                                           "\'" + alumni_program + "\'" +","
                                           "\'" + alumni_degree + "\'" +
                               ")")
            except pyodbc.IntegrityError:
                print("Primary Key Violation")
                continue;
            educations = alumni.alumni_education
            jobs = alumni.job_history
            skills = alumni.skill_list
            for skill in skills:
                cursor.execute("Insert Into dbo.Skills(alumni_id,skill_names) " +
                            "Values(" + "\'" + alumni.id + "\'" + ","
                                        "\'" + skill + "\'" +
                            ")")
            for education in educations:
                print(education.degree + education.fieldOfStudy + ' ' + education.school_name + ' ' + education.graduation_date)
                cursor.execute("Insert Into dbo.Education(alumni_id,education_name,school,degree) " +
                            "Values(" + "\'" + alumni.id + "\'" + ","
                                        "\'" + education.fieldOfStudy + "\'" + ","
                                        "\'" + education.school_name + "\'" + ","
                                        "\'" + education.degree + "\'" 
                            ")")
                if education.graduation_date != "":
                    cursor.execute("Update dbo.Education Set graduation_date = " + "\'" + education.graduation_date + "\'" + "WHERE alumni_id = " + "\'" +
                                   alumni.id + "\'")
            for job in jobs:
                cursor.execute("Insert Into dbo.Jobs(title,company,alumni_id) " +
                            "Values(" + "\'" + job.title + "\'" + ","
                                        "\'" + job.company + "\'" + ","
                                        "\'" + alumni.id + "\'" +
                               ")")
                if job.startDate != "":
                    job.startDate = job.startDate.replace(".", "-")#Replace the dot with a dash for the date format
                    job.startDate = job.startDate + "-01"
                    cursor.execute(
                        "Update dbo.Jobs Set startdate = " + "\'" + job.startDate + "\'" + "WHERE alumni_id = " + "\'" +
                        alumni.id + "\'" + "and title =" + "\'" + job.title + "\'" + "and company =" + "\'" + job.company + "\'")
                if job.endDate != "Now":
                    job.endDate = job.endDate.replace(".","-")
                    job.endDate = job.endDate + "-01"
                if job.endDate != "Now":
                    cursor.execute(
                        "Update dbo.Jobs Set enddate = " + "\'" + job.endDate + "\'" + "WHERE startdate = " + "\'" +
                        job.startDate + "\'" + "and title =" + "\'" + job.title + "\'" + "and company =" + "\'" + job.company + "\'" +
                        "and alumni_id =" + "\'" + alumni.id + "\'")
                print(job.title + ' ' + job.company + ' ' + job.startDate + ' ' + job.endDate)

if __name__ == "__main__":
    insert_one()
    cnxn.commit()


