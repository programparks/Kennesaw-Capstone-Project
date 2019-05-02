# coding=utf-8

import sys
# from urllib import unquote
from urllib import parse

import requests
import re
from lxml import etree

from bs4 import BeautifulSoup

import os, json, time

CREDIT_GRADE = {  # 芝麻信用
    'EXCELLENT': '极好',
    'VERY_GOOD': '优秀',
    'GOOD': '良好',
    'ACCEPTABLE': '中等',
    'POOR': '较差'
}
LINKS_FINISHED = []  # 已抓取的linkedin用户


def login(laccount, lpassword):
    """ 根据账号密码登录linkedin """
    s = requests.Session()
    r = s.get('https://www.linkedin.com/uas/login')
    tree = etree.HTML(r.content)
    loginCsrfParam = ''.join(tree.xpath('//input[@id="loginCsrfParam-login"]/@value'))
    csrfToken = ''.join(tree.xpath('//input[@id="csrfToken-login"]/@value'))
    sourceAlias = ''.join(tree.xpath('//input[@id="sourceAlias-login"]/@value'))
    isJsEnabled = ''.join(tree.xpath('//input[@name="isJsEnabled"]/@value'))
    source_app = ''.join(tree.xpath('//input[@name="source_app"]/@value'))
    tryCount = ''.join(tree.xpath('//input[@id="tryCount"]/@value'))
    clickedSuggestion = ''.join(tree.xpath('//input[@id="clickedSuggestion"]/@value'))
    signin = ''.join(tree.xpath('//input[@name="signin"]/@value'))
    session_redirect = ''.join(tree.xpath('//input[@name="session_redirect"]/@value'))
    trk = ''.join(tree.xpath('//input[@name="trk"]/@value'))
    fromEmail = ''.join(tree.xpath('//input[@name="fromEmail"]/@value'))

    payload = {
        'isJsEnabled': isJsEnabled,
        'source_app': source_app,
        'tryCount': tryCount,
        'clickedSuggestion': clickedSuggestion,
        'session_key': laccount,
        'session_password': lpassword,
        'signin': signin,
        'session_redirect': session_redirect,
        'trk': trk,
        'loginCsrfParam': loginCsrfParam,
        'fromEmail': fromEmail,
        'csrfToken': csrfToken,
        'sourceAlias': sourceAlias
    }
    s.post('https://www.linkedin.com/uas/login-submit', data=payload)
    htmlStr = s.get('https://www.linkedin.com/in/jgzheng/').text
    soup = BeautifulSoup(htmlStr, 'html.parser')
    content = parse.unquote(htmlStr).replace('&quot;', '"')
    return s


def getContent(s, url):
    htmlStr = s.get(url).text
    content = parse.unquote(htmlStr).replace('&quot;', '"')
    return content


def parseAndExport(content, userProfileLink):
    data = {}
    data['education'] = []
    data['nameUrlId'] = []
    data['skills'] = []
    data['jobHistory'] = []
    enddate = ''

    profile_txt = ' '.join(re.findall('(\{[^\{]*?profile\.Profile"[^\}]*?\})', content))
    firstname = re.findall('"firstName":"(.*?)"', profile_txt)
    lastname = re.findall('"lastName":"(.*?)"', profile_txt)
    educations = re.findall('(\{[^\{]*?profile\.Education"[^\}]*?\})', content)
    skills = re.findall('(\{[^\{]*?com.linkedin.voyager.identity.profile.Skill[^\}]*?\})', content)

    if isAlumni(educations):
        path = "people_info"
        isExists = os.path.exists(path)
        if not isExists:
            os.makedirs(path)

        f = open(path + "/" + firstname[0] + lastname[0] + '.txt', 'w', encoding='UTF8')
        json_file = open(path + "/" + firstname[0] + lastname[0] + 'Json' + '.txt', 'w', encoding='UTF8')

        f.write("Skills: \n")
        for one in skills:
            one = one.replace("&quot;", "\"")
            skill_name = re.findall('\"name\":"(.*?)"', one)
            if (skill_name.__len__() > 0):
                line = '    ' + skill_name[0]
                f.write(line + "\n")
                data['skills'].append(
                    {
                        'skill': skill_name[0]
                    }
                )
        if firstname and lastname:
            line = 'Name: %s%s   %s' % (lastname[0], firstname[0], userProfileLink)
            print(line)
            f.write(line + '\n')
            alumniId = userProfileLink.replace('https://www.linkedin.com/in/','')
            alumniId = alumniId.replace('/','')
            data['nameUrlId'].append(
                {
                    'firstName': firstname[0],
                    'lastName': lastname[0],
                    'linkedInUrl': userProfileLink,
                    'id': alumniId
                }
            )
            summary = re.findall('"summary":"(.*?)"', profile_txt)
            if summary:
                line = 'Summary: %s' % summary[0]
                print(line)
                f.write(line + '\n')

            occupation = re.findall('"headline":"(.*?)"', profile_txt)
            if occupation:
                line = 'occupation: %s' % occupation[0]
                print(line)
                f.write(line + '\n')

            locationName = re.findall('"locationName":"(.*?)"', profile_txt)
            if locationName:
                line = 'location: %s' % locationName[0]
                print(line)
                f.write(line + '\n')

        if educations:
            line = 'Education Background:'
            print(line)
            f.write(line + '\n')
            education_counter = 0
            last_school = ""
            last_school_time = ""
            last_field = ""
            last_degree = ""
        for one in educations:
            schoolName = re.findall('"schoolName":"(.*?)"',one)
            fieldOfStudy = re.findall('"fieldOfStudy":"(.*?)"',one)
            degreeName = re.findall('"degreeName":"(.*?)"',one)
            timePeriod = re.findall('"timePeriod":"(.*?)"', one)
            schoolTime = ''

            if timePeriod:
                startdate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,startDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))

                enddate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,endDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))

                start_year = re.findall('"year":(\d+)', startdate_txt)
                start_month = re.findall('"month":(\d+)', startdate_txt)
                end_year = re.findall('"year":(\d+)', enddate_txt)
                end_month = re.findall('"month":(\d+)', enddate_txt)
                startdate = ''
                if start_year:
                    startdate += '%s' % start_year[0]
                    if start_month:
                        startdate += '.%s' % start_month[0]
                enddate = ''
                if end_year:
                    enddate += '%s' % end_year[0]
                    if end_month:
                        enddate += '.%s' % end_month[0]
                if len(startdate) > 0 and len(enddate) == 0:
                    enddate = 'Now'
                schoolTime += '   %s ~ %s' % (startdate, enddate)
            if schoolName:
                fieldOfStudy = '   %s' % fieldOfStudy[0] if fieldOfStudy else ''
                degreeName = '   %s' % degreeName[0] if degreeName else ''
                line = '    %s %s %s %s' % (schoolName[0], schoolTime, fieldOfStudy, degreeName)
                print(line)
                data['education'].append(
                    {
                        'degree': degreeName,
                        'field': fieldOfStudy,
                        'schoolName': schoolName[0],
                        'endDate': enddate
                    }
                )
                f.write(line + '\n')
        position = re.findall('(\{[^\{]*?profile\.Position"[^\}]*?\})', content)
        if position:
            line = 'Working Experience:'
            print(line)
            f.write(line + '\n')
        for one in position:
            companyName = re.findall('"companyName":"(.*?)"', one)
            title = re.findall('"title":"(.*?)"', one)
            locationName = re.findall('"locationName":"(.*?)"', one)
            timePeriod = re.findall('"timePeriod":"(.*?)"', one)
            positionTime = ''
            if timePeriod:
                startdate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,startDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))
                enddate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,endDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))
                start_year = re.findall('"year":(\d+)', startdate_txt)
                start_month = re.findall('"month":(\d+)', startdate_txt)
                end_year = re.findall('"year":(\d+)', enddate_txt)
                end_month = re.findall('"month":(\d+)', enddate_txt)
                startdate = ''
                if start_year:
                    startdate += '%s' % start_year[0]
                    if start_month:
                        startdate += '.%s' % start_month[0]
                enddate = ''
                if end_year:
                    enddate += '%s' % end_year[0]
                    if end_month:
                        enddate += '.%s' % end_month[0]
                if len(startdate) > 0 and len(enddate) == 0:
                    enddate = 'Now'
                positionTime += '   %s ~ %s' % (startdate, enddate)
            if companyName:
                title = '   %s' % title[0] if title else ''
                locationName = '   %s' % locationName[0] if locationName else ''
                line = '    %s %s %s %s' % (companyName[0], positionTime, title, locationName)
                print(line)
                f.write(line + '\n')
                data['jobHistory'].append(
                    {
                        'title': title,
                        'company': companyName[0],
                        'startDate': startdate,
                        'endDate': enddate,
                    }
                )

        publication = re.findall('(\{[^\{]*?profile\.Publication"[^\}]*?\})', content)
        if publication:
            line = 'Publications:'
            print(line)
            f.write(line + '\n')
        for one in publication:
            name = re.findall('"name":"(.*?)"', one)
            publisher = re.findall('"publisher":"(.*?)"', one)
            if name:
                line = '    %s %s' % (name[0], '   Publishing House: %s' % publisher[0] if publisher else '')
                print(line)
                f.write(line + '\n')

        honor = re.findall('(\{[^\{]*?profile\.Honor"[^\}]*?\})', content)
        if honor:
            line = 'Honor&Awards:'
            print(line)
            f.write(line + '\n')
        for one in honor:
            title = re.findall('"title":"(.*?)"', one)
            issuer = re.findall('"issuer":"(.*?)"', one)
            issueDate = re.findall('"issueDate":"(.*?)"', one)
            issueTime = ''
            if issueDate:
                issueDate_txt = ' '.join(
                    re.findall('(\{[^\{]*?"\$id":"%s"[^\}]*?\})' % issueDate[0].replace('(', '\(').replace(')', '\)'),
                               content))
                year = re.findall('"year":(\d+)', issueDate_txt)
                month = re.findall('"month":(\d+)', issueDate_txt)
                if year:
                    issueTime += '   Time: %s' % year[0]
                    if month:
                        issueTime += '.%s' % month[0]
            if title:
                line = '    %s %s %s' % (title[0], '   Author: %s' % issuer[0] if issuer else '', issueTime)
                print(line)
                f.write(line + '\n')

        organization = re.findall('(\{[^\{]*?profile\.Organization"[^\}]*?\})', content)
        if organization:
            line = 'Involved Organization:'
            print(line)
            f.write(line + '\n')
        for one in organization:
            name = re.findall('"name":"(.*?)"', one)
            timePeriod = re.findall('"timePeriod":"(.*?)"', one)
            organizationTime = ''
            if timePeriod:
                startdate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,startDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))
                enddate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,endDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))
                start_year = re.findall('"year":(\d+)', startdate_txt)
                start_month = re.findall('"month":(\d+)', startdate_txt)
                end_year = re.findall('"year":(\d+)', enddate_txt)
                end_month = re.findall('"month":(\d+)', enddate_txt)
                startdate = ''
                if start_year:
                    startdate += '%s' % start_year[0]
                    if start_month:
                        startdate += '.%s' % start_month[0]
                enddate = ''
                if end_year:
                    enddate += '%s' % end_year[0]
                    if end_month:
                        enddate += '.%s' % end_month[0]
                if len(startdate) > 0 and len(enddate) == 0:
                    enddate = 'Now'
                organizationTime += '   %s ~ %s' % (startdate, enddate)
            if name:
                line = '    %s %s' % (name[0], organizationTime)
                print(line)
                f.write(line + '\n')

        patent = re.findall('(\{[^\{]*?profile\.Patent"[^\}]*?\})', content)
        if patent:
            line = 'Patent:'
            print(line)
            f.write(line + '\n')
        for one in patent:
            title = re.findall('"title":"(.*?)"', one)
            issuer = re.findall('"issuer":"(.*?)"', one)
            url = re.findall('"url":"(http.*?)"', one)
            number = re.findall('"number":"(.*?)"', one)
            localizedIssuerCountryName = re.findall('"localizedIssuerCountryName":"(.*?)"', one)
            issueDate = re.findall('"issueDate":"(.*?)"', one)
            patentTime = ''
            if issueDate:
                issueDate_txt = ' '.join(
                    re.findall('(\{[^\{]*?"\$id":"%s"[^\}]*?\})' % issueDate[0].replace('(', '\(').replace(')', '\)'),
                               content))
                year = re.findall('"year":(\d+)', issueDate_txt)
                month = re.findall('"month":(\d+)', issueDate_txt)
                day = re.findall('"day":(\d+)', issueDate_txt)
                if year:
                    patentTime += '   Time: %s' % year[0]
                    if month:
                        patentTime += '.%s' % month[0]
                        if day:
                            patentTime += '.%s' % day[0]
            if title:
                line = '    %s %s %s %s %s %s' % (
                    title[0], '   Author: %s' % issuer[0] if issuer else '', '   NO: %s' % number[0] if number else '',
                    '   Country: %s' % localizedIssuerCountryName[0] if localizedIssuerCountryName else '', patentTime,
                    '   Detail: %s' % url[0] if url else '')
                print(line)
                f.write(line + '\n')

        project = re.findall('(\{[^\{]*?profile\.Project"[^\}]*?\})', content)
        if project:
            line = 'Projects:'
            print(line)
            f.write(line + '\n')
        for one in project:
            title = re.findall('"title":"(.*?)"', one)
            description = re.findall('"description":"(.*?)"', one)
            timePeriod = re.findall('"timePeriod":"(.*?)"', one)
            projectTime = ''
            if timePeriod:
                startdate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,startDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))
                enddate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,endDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))
                start_year = re.findall('"year":(\d+)', startdate_txt)
                start_month = re.findall('"month":(\d+)', startdate_txt)
                end_year = re.findall('"year":(\d+)', enddate_txt)
                end_month = re.findall('"month":(\d+)', enddate_txt)
                startdate = ''
                if start_year:
                    startdate += '%s' % start_year[0]
                    if start_month:
                        startdate += '.%s' % start_month[0]
                enddate = ''
                if end_year:
                    enddate += '%s' % end_year[0]
                    if end_month:
                        enddate += '.%s' % end_month[0]
                if len(startdate) > 0 and len(enddate) == 0:
                    enddate = 'Now'
                projectTime += '   Time: %s ~ %s' % (startdate, enddate)
            if title:
                line = '    %s %s %s' % (
                title[0], projectTime, '   Description: %s' % description[0] if description else '')
                print(line)
                f.write(line + '\n')

        volunteer = re.findall('(\{[^\{]*?profile\.VolunteerExperience"[^\}]*?\})', content)
        if volunteer:
            line = 'Volunteer:'
            print(line)
            f.write(line + '\n')
        for one in volunteer:
            companyName = re.findall('"companyName":"(.*?)"', one)
            role = re.findall('"role":"(.*?)"', one)
            timePeriod = re.findall('"timePeriod":"(.*?)"', one)
            volunteerTime = ''
            if timePeriod:
                startdate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,startDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))
                enddate_txt = ' '.join(re.findall(
                    '(\{[^\{]*?"\$id":"%s,endDate"[^\}]*?\})' % timePeriod[0].replace('(', '\(').replace(')', '\)'),
                    content))
                start_year = re.findall('"year":(\d+)', startdate_txt)
                start_month = re.findall('"month":(\d+)', startdate_txt)
                end_year = re.findall('"year":(\d+)', enddate_txt)
                end_month = re.findall('"month":(\d+)', enddate_txt)
                startdate = ''
                if start_year:
                    startdate += '%s' % start_year[0]
                    if start_month:
                        startdate += '.%s' % start_month[0]
                enddate = ''
                if end_year:
                    enddate += '%s' % end_year[0]
                    if end_month:
                        enddate += '.%s' % end_month[0]
                if len(startdate) > 0 and len(enddate) == 0:
                    enddate = 'Now'
                volunteerTime += '   Time: %s ~ %s' % (startdate, enddate)
            if companyName:
                line = '    %s %s %s' % (companyName[0], volunteerTime, '   role: %s' % role[0] if role else '')
                print(line)
                f.write(line + '\n')
        f.close()
        json.dump(data,json_file)
        json_file.close()

def writePeopleList(s, s_url):
    idList = list()
    pageNum = 1
    count = 0

    f = open('linkedin_people_url.txt', 'w', encoding='UTF8')

    while pageNum > 0:
        count = pageNum
        htmlStr = s.get(s_url).text
        content = parse.unquote(htmlStr).replace('&quot;', '"')
        soup = BeautifulSoup(htmlStr, 'html.parser')
        dataBlock = soup.find_all("code")
        for k in dataBlock:
            kText = k.get_text()
            if kText.find("metadata") > 0:
                jsData = json.loads(kText)
                for item in jsData["included"]:
                        if "$id" in item:
                            idTags = item["$id"]
                            if "urn:li:fs_miniProfile" in idTags:
                                sp = idTags.split(",")[0]
                                id = sp.split(":")[3]
                                url = "https://www.linkedin.com/in/" + id
                                if url not in idList:
                                    idList.append(url)
                                    f.write(url + "/\n")
                                    print(url)
        pageNum -= 1
    f.close()
    if len(idList) == 0:
        print("No people list has been found!")
    return idList

def getPeopleInfo(s):
    # check the linkedin_people_url.txt file
    isExistsFile = os.path.exists("linkedin_people_url.txt")
    if not isExistsFile:
        fp = open("linkedin_people_url.txt", "w")
        fp.close()

    with open("linkedin_people_url.txt", "r", encoding="UTF8") as f:
        for line in f:
            url = line.strip()
            content = getContent(s, url)
            parseAndExport(content, url)


def inputParam():
    # prompt input info
    print("Please input keywords of search:")
    params = sys.stdin.readline().strip("\n")
    if params.startswith("https://www.linkedin.com"):
        url = params
    else:
        params = params.replace(" ", "%20")
        url = "https://www.linkedin.com/search/results/index/?keywords=" + params + "&origin=GLOBAL_SEARCH_HEADER&page=1"
    return url


def crawl(s,search_string,num):
    if num == "one":
        url = "https://www.linkedin.com/search/results/index/?keywords=" + search_string + "&origin=GLOBAL_SEARCH_HEADER&page=1"
        writePeopleList(s,url)#Write people list to the file
        getPeopleInfo(s) #Parse and export data to JSON
    if num == "many":
        url = "https://www.linkedin.com/search/results/index/?keywords=" + search_string + "&origin=GLOBAL_SEARCH_HEADER&page="
        writeMany(s,url)
        getPeopleInfo(s)


global_search_string = ""
def isAlumni(education_list):
    education_found = False
    field_found = False
    for i in education_list:
        fieldOfStudy = re.findall('"fieldOfStudy":"(.*?)"', i)
        for j in range(0,len(fieldOfStudy)):
            field = fieldOfStudy[j]
            if field.lower() in global_search_string.lower():
                field_found = True
                break
        education = i
        if "kennesaw" in education.lower():
            education_found = True
    if(education_found) == True:
        return True


def writeMany(s, s_url):
    pageNum = 1
    idList = list()
    count = 0
    f = open('linkedin_people_url.txt', 'w', encoding='UTF8')

    while True:
        nextUrl = s_url + str(pageNum)
        htmlStr = s.get(nextUrl).text
        content = parse.unquote(htmlStr).replace('&quot;', '"')
        soup = BeautifulSoup(htmlStr, 'html.parser')
        dataBlock = soup.find_all("code")

        for k in dataBlock:
            kText = k.get_text()
            if kText.find("metadata") > 0:
                jsData = json.loads(kText)
                for item in jsData["included"]:
                        if "$id" in item:
                            idTags = item["$id"]
                            if "urn:li:fs_miniProfile" in idTags:
                                sp = idTags.split(",")[0]
                                id = sp.split(":")[3]
                                url = "https://www.linkedin.com/in/" + id
                                if url not in idList:
                                    idList.append(url)
                                    f.write(url + "/\n")
                                    print(url)

        if len(idList) == 0:
            print("No people list has been found!")
            print(pageNum)
            f.close()
            return idList

        else:
            pageNum = pageNum+1
            idList.clear()


if __name__ == '__main__':
    search_file = open('search_strings.txt', 'r', encoding='UTF8')
