import json
import pyodbc
import glob
import sys
# from urllib import unquote
from urllib import parse
import requests
import re
from lxml import etree

from bs4 import BeautifulSoup

import os, json, time

from Crawler import login,getContent,parseAndExport

from Insert import Alumni,Education,Job

from Insert import userName
from Insert import passWD

server = 'itcapstone.database.windows.net'

cnxn = pyodbc.connect('Driver={ODBC Driver 13 for SQL Server};Server=tcp:itcapstone.database.windows.net,1433;Database=CAPSTONE;Uid=capstone@itcapstone;Pwd=Alumnidatabase!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
cursor = cnxn.cursor()



#Check if education in database
def doesEducationExist(education,alumni_id):
    cursor.execute("Select education_name,school,degree,graduation_date FROM dbo.Education WHERE alumni_id = " "\'" + alumni_id + "\'")
    education_rows = cursor.fetchall()
    for row in education_rows:
        education_result = row.education_name
        school_result = row.school
        degree_result = row.degree
        graduation_result = str(row.graduation_date)
        graduation_result = graduation_result[0:4]
        if ((education.fieldOfStudy == education_result) and (education.school_name == school_result) and
            (education.degree == degree_result)):
            return True
    return False
#Check if skill exists
def doesSkillExist(skill,alumni_id):
    cursor.execute("Select skill_names FROM dbo.Skills WHERE alumni_id = " "\'" + alumni_id + "\'")
    skill_rows = cursor.fetchall()
    for row in skill_rows:
        skill_result = row.skill_names
        if skill == skill_result:
            return True
    return False

#Check if job exists
def doesJobExist(job,alumni_id):
    cursor.execute("Select title, company, startDate, endDate FROM dbo.Jobs WHERE alumni_id = " "\'" + alumni_id + "\'")
    job_rows = cursor.fetchall()
    for row in job_rows:
        title_result = row.title
        company_result = row.company
        if job.title == title_result and job.company == company_result:
            return True
    return False


def update_database():
    search_file = open('search_strings.txt', 'r', encoding='UTF8')
    s = login(userName, passWD)

    #get linkedin urls from database
    cursor.execute("select first_name, last_name, linkedid_link from dbo.Alumni")
    rows = cursor.fetchall();
    AlumniList = []
    #update files
    for row in rows:
        url = row.linkedid_link.strip()
        content = getContent(s,url)
        parseAndExport(content,url)

    #update database
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
                education_object = Education(degree, field, schoolName, graduation_date)
                education_list.append(education_object)
            for position in data['jobHistory']:
                title = position['title']
                company = position['company']
                startDate = position['startDate']
                endDate = position['endDate']
                job_object = Job(title, company, startDate, endDate)
                job_list.append(job_object)
            for skill in data['skills']:
                skill_name = skill['skill']
                skill_list.append(skill_name)
            json_file.close()
            os.remove(filename)
        AlumniList.append(Alumni(first_name, last_name, id, linked_in, education_list, job_list, skill_list))

    for alumni in AlumniList:
        cursor.execute("Update dbo.Alumni set first_name = " + '\'' + alumni.first_name + "\'" + "WHERE alumni_id = " + "\'" + alumni.id + "\'")
        educations = alumni.alumni_education
        jobs = alumni.job_history

        for education in alumni.alumni_education:
            education_exists = doesEducationExist(education,alumni.id) #Insert if it isn't already in the database
            if education_exists != True:
                cursor.execute("Insert Into dbo.Education(alumni_id,education_name,school,degree,graduation_date) " +
                               "Values(" + "\'" + alumni.id + "\'" + ","
                                           "\'" + education.fieldOfStudy + "\'" + ","
                                           "\'" + education.school_name + "\'" + ","
                                           "\'" + education.degree + "\'" + "," +
                               "\'" + education.graduation_date + "\'"
                               ")")
        for skill in alumni.skill_list:
            skill_exists = doesSkillExist(skill,alumni.id)
            if skill_exists != True:
                cursor.execute("Insert Into dbo.Skills(alumni_id,skill_names) " +
                               "Values(" + "\'" + alumni.id + "\'" + ","
                                            "\'" + skill + "\'"
                               ")")

        for job in jobs:
            job_exists = doesJobExist(job,alumni.id)
            if job_exists == True:
                if job.startDate != "":
                    job.startDate = job.startDate.replace(".", "-")
                    job.startDate = job.startDate + "-01"
                    cursor.execute(
                        "Update dbo.Jobs Set startdate = " + "\'" + job.startDate + "\'" + "WHERE alumni_id = " + "\'" +
                        alumni.id + "\'" + "and title =" + "\'" + job.title + "\'" + "and company =" + "\'" + job.company + "\'")
                if job.endDate != "Now":
                    job.endDate = job.endDate.replace(".", "-")
                    job.endDate = job.endDate + "-01"
                if job.endDate != "Now":
                    cursor.execute(
                        "Update dbo.Jobs Set enddate = " + "\'" + job.endDate + "\'" + "WHERE startdate = " + "\'" +
                        job.startDate + "\'" + "and title =" + "\'" + job.title + "\'" + "and company =" + "\'" + job.company + "\'" +
                        "and alumni_id =" + "\'" + alumni.id + "\'")


            if job_exists != True:#Insert job if it doesn't already exist
                cursor.execute("Insert Into dbo.Jobs(title,company,alumni_id) " +
                               "Values(" + "\'" + job.title + "\'" + ","
                                           "\'" + job.company + "\'" + ","
                                           "\'" + alumni.id + "\'" +
                               ")")
                if job.startDate != "":
                    job.startDate = job.startDate.replace(".", "-")
                    job.startDate = job.startDate + "-01"
                    cursor.execute(
                        "Update dbo.Jobs Set startdate = " + "\'" + job.startDate + "\'" + "WHERE alumni_id = " + "\'" +
                        alumni.id + "\'" + "and title =" + "\'" + job.title + "\'" + "and company =" + "\'" + job.company + "\'")
                if job.endDate != "Now":
                    job.endDate = job.endDate.replace(".", "-")
                    job.endDate = job.endDate + "-01"
                if job.endDate != "Now":
                    cursor.execute(
                        "Update dbo.Jobs Set enddate = " + "\'" + job.endDate + "\'" + "WHERE startdate = " + "\'" +
                        job.startDate + "\'" + "and title =" + "\'" + job.title + "\'" + "and company =" + "\'" + job.company + "\'" +
                        "and alumni_id =" + "\'" + alumni.id + "\'")
update_database()
cnxn.commit()

