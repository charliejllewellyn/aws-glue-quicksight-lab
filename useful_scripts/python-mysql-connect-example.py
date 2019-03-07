import boto3
import os
import sys
import re

for f in os.listdir('.'):
    if re.match('glue-python-libs.*', f):
        custom_module = f
sys.path.insert(0, custom_module + '/mysql.zip')

import mysql.connector

s3 = boto3.resource('s3')
s3.Bucket('cjl-temp-dub').download_file('employee.sql', 'employee.sql')

cnx = mysql.connector.connect(user='dbuser', password='password12345',
                              host='3.8.2.93',database='employees')

cursor = cnx.cursor()
file = open('employee.sql', 'r')
for sql in file.readlines():
    if not re.match('^--.*', sql):
        if sql != None:
            if not re.match('\s+', sql):
                print("SQL statement: '" + sql + "'")
                cursor.execute(sql)
#cnx.commit()
print('COMPLETE')
