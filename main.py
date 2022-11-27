import tweepy
import psycopg2 
import pandas as pd
import datetime
from sqlalchemy import create_engine
from email.message import EmailMessage
import ssl
import smtplib
import os

    #pip install "prefect==1.*"

#week_ago = datetime.date.today() - datetime.timedelta(days=7)
#yester = datetime.date.today() - datetime.timedelta(days=1)

def mail_note(a,b,c,d):
    now = datetime.datetime.now()

    current_time = now.strftime("%H:%M")
    today = datetime.date.today()


    email_sender = 'georgemichaeldagogomaynard@gmail.com'
    email_password = os.environ.get("EMAIL_PASSWORD")
    email_receiver = ['michaeligbomezie@gmail.com','georgemichaeldagogo@gmail.com']
    

    #'michaeligbomezie@gmail.com',


    subject = "Database update report for {}".format(today)
    body = "Database was successfully updated at {now_time} \n \n {new_rows} new rows were added \n \n Database rows currently at {data_count} \n \n Distinct rows of tweets in database is {distinct} \n \n Here is a sample of the last 5 updated rows in the database \n \n {sample}".format(now_time=current_time,new_rows=a,data_count=b,distinct=c,sample=d)

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context = context) as smtp:
        smtp.login(email_sender,email_password)
        smtp.sendmail(email_sender,email_receiver, em.as_string())


def get_data():
    today = datetime.date.today()
    api_key = os.environ.get("API_KEY")
    api_key_secret = os.environ.get("API_KEY_SECRET")
    access_token = os.environ.get("ACCESS_TOKEN")
    access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
    auth = tweepy.OAuthHandler(api_key,api_key_secret)
    auth.set_access_token(access_token,access_token_secret)

    api = tweepy.API(auth)

    keywords = ['Buhari OR APC OR  PeterObi OR Tinubu OR PDP OR Atiku OR LabourParty']
    #keywords = ['Buhari','APC', 'PeterObi','Tinubu','Atiku']
    #it seems the api does not return every tweet containing at least one or every keyword, it returns the only tweets that contains every keyword
    #solution was to use the OR in the keywords string as this is for tweets search only and might give errors in pure python
    limit = 10000

    tweets = tweepy.Cursor(api.search_tweets, q = keywords,count = 200, tweet_mode = 'extended',geocode='9.0820,8.6753,450mi', until=today).items(limit)

    columns = ['time_created', 'screen_name','name', 'tweet','loca_tion', 'descrip_tion','verified','followers', 'source','geo_enabled','retweet_count','truncated','lang','likes']
    data = []


    for tweet in tweets:
        data.append([tweet.created_at, tweet.user.screen_name, tweet.user.name,tweet.full_text, tweet.user.location, tweet.user.description,tweet.user.verified,tweet.user.followers_count,tweet.source,tweet.user.geo_enabled,tweet.retweet_count,tweet.truncated,tweet.lang,tweet.favorite_count])
        
    df = pd.DataFrame(data , columns=columns)
    df = df[~df.tweet.str.contains("RT")]
    #removes retweeted tweets
    df = df.reset_index(drop = True)
    print(df.time_created)


    conn_string = os.environ.get("CONN_STRING")
    
    db = create_engine(conn_string)
    conn = db.connect()

    df.to_sql('election', con=conn, if_exists='append',
            index=False)
    conn = psycopg2.connect(database=os.environ.get("DATABASE"),
                                user=os.environ.get("USER"), 
                                password=os.environ.get("PASSWORD"),
                                host=os.environ.get("HOST")
        )
    conn.autocommit = True
    cursor = conn.cursor()
    
    sql1 = '''DELETE FROM election WHERE time_created < current_timestamp - interval '8' day;'''
    cursor.execute(sql1)

    sql2 = '''DELETE FROM election T1 USING election T2 
    WHERE T1.ctid < T2.ctid 
    AND  T1.tweet = T2.tweet;'''
    #The “CTID” field is a field that exists in every PostgresSQL table, 
    #it is always unique for each and every record in the table
    cursor.execute(sql2)

    sql3 = '''SELECT COUNT(*) FROM election;'''
    cursor.execute(sql3)
    for q in cursor.fetchall():
        q

    sql4 = '''SELECT DISTINCT(COUNT(tweet)) FROM election;'''
    cursor.execute(sql4)
    for w in cursor.fetchall():
        w

    sql5 = '''SELECT * FROM election ORDER BY time_created DESC LIMIT 5;'''
    cursor.execute(sql5)
    for e in cursor.fetchall():
        e
    # conn.commit()
    conn.close()
    mail_note(len(df),q,w,e)


get_data()
