import praw
import urllib2

## Searches CrunchyRoll.com for an anime title, returns any it finds in a list.
def CrunchyUrl(anime_titles):
    crunchy_url = []
    for title in anime_titles:
        url = ("http://crunchyroll.com/search?q=%s" % title.replace(" ", "+").lower())
        req = urllib2.Request(url, headers={'User-Agent': "Anime Browser"})

        html_req = urllib2.urlopen(req)
        html_source = html_req.readlines()
    
        count = 0
        crunchy_title = ""
        for line in html_source:
            if "<a href" in line and "\" class=\"clearfix\">" in line:
                if count == 0:
                    crunchy_title = line.split("\"")[1]
                    print crunchy_title
                    count += 1
        if crunchy_title == "":
            crunchy_url.append(False)
        else:
            crunchy_url.append("http://crunchyroll.com%s" % crunchy_title)
    return crunchy_url

## The only reason bot isn't currently running -.- waiting on MAL to send me a user agent
def MALUrl(anime_titles):
    for title in anime_titles:
        url = ("http://myanimelist.net/api/anime/search.xml?q=%s" + title)
        req = urllib2.Request(url, headers={'User-Agent': ""})

        xml_req = urllib2.urlopen(req)
        xml_source = xml_req.readlines()

        for line in xml_source:
            print line
            
## Uses AnimeAdvice.me to check for similar anime.
def GetSimilar(MAL_urls):
    index = 0
    similar_urls = []
    for url in MAL_urls:
        anime_id = url.split("/")[4]

        url = ("http://animeadvice.me/similarity/?name=id%s-anime" % (anime_id))
        print url
        req = urllib2.Request(url, headers={'User-Agent':'Anime Browser'})

        html_req = urllib2.urlopen(req)
        html_source = html_req.readlines()

        count = 0
        for line in html_source:
            if "http://myanimelist.net" in line and count == 0:
                similar_urls.append(line.split("\"")[3])
                count += 1
        if count == 0:
            similar_urls.append(False)
    return similar_urls

## Login to Reddit
def RedditLogin():
    r = praw.Reddit('animelinkbot by /u/Sc1F1')
    r.login('animelinkbot', 'PRIVATE')

    return r

## Checks Anime title list for any matches in the comment, returns any it finds in a list
def CheckAnimeTitles(comment):
    anime_list = open("RedditBotAnimeList.txt", 'r')
    anime_title_list = anime_list.readlines()
    anime_list.close()

    reply_title = []
    should_reply = False
    for title in anime_title_list:
        anime_title = title.replace("\n", "")
        if unicode(anime_title, "utf-8") in comment:
            ##print anime_title
            reply_title.append(anime_title)
            should_reply = True
        

    if should_reply == True:
        return reply_title
    else:
        return False
    
## Formats all information for a reply, only adds information if it needs to.
def PrepareReply(anime_titles, MAL_urls, crunchy_urls, similar_urls, need_MAL, need_crunch, need_similar, parent_check):
    comment_reply = "***"
    index = 0
    for title in anime_titles:
        if parent_check != False:
            comment_reply = comment_reply + ("\n\n* %s" % title)
            if need_MAL[index] != False:
                comment_reply = comment_reply + (" - [MAL](%s)" % MAL_urls[index])
            if need_crunch[index] != False:
                comment_reply = comment_reply + (" - [CR](%s)" % crunchy_urls[index])
            if need_similar[index] != False and similar_urls[index] not in comment_reply:
                comment_reply = comment_reply + (" - Similar Anime: [MAL](%s)" % similar_urls[index])
        index += 1
    comment_reply = comment_reply + ("\n\n***\nPlease contact /u/Sc1F1 if you notice any bugs, incorrect links or have any questions.")
    return comment_reply


## If any URL returns true, Bot will reply
def CheckReply(need_MAL, need_crunch, parent_check):
    ##Both must be True for function to return True
    need_reply = False
    reply_needed = False
    for value in parent_check:
        if value == True:
            need_reply = True
    if need_reply == True:
        for value in need_MAL:
            if value == True:
                reply_needed = True
        for value in need_crunch:
            if value == True:
                reply_needed = True

    return reply_needed

## Checks if url is in comment already
def CheckUrl(comment, url_list):
    need_url = []
    for url in url_list:
        if url == False or url in comment:
            need_url.append(False)
        else:
            need_url.append(True)
    return need_url

## Currently only checks the immediate parent, need to check all up to start of thread
def CheckParent(comment, anime_titles, already_done):
    parent = r.get_info(thing_id=comment.parent_id)
    pass_check = []
    for title in anime_titles:
        if parent.id in already_done and title in parent.body:
            pass_check.append(False)
        elif title in parent.body and parent.author.name == 'animelinkbot':
            pass_check.append(False)
        else:
            pass_check.append(True)
    return pass_check


## Need to rewrite and split into seperate functions
def CommentGet(r):
    already_done = set()
    while(1):
        multi_reddits = r.get_subreddit('animesuggest')
        multi_reddits_comments = multi_reddits.get_comments()

        for comment in multi_reddits_comments:
            if comment.id not in already_done and comment.author.name != 'animelinkbot':
                already_done.add(comment.id)
                anime_titles = CheckAnimeTitles(comment.body)
                parent_check = CheckParent(comment, anime_titles, already_done)
                if anime_titles != False:
                    MAL_urls = MALUrl(anime_titles)
                    crunchy_urls = CrunchyUrl(anime_titles)
                    need_MAL = CheckUrl(comment.body, MAL_urls)
                    need_crunch = CheckUrl(comment.body, crunchy_urls)
                    need_reply = CheckReply(need_MAL, need_crunch, parent_check)
                    if need_reply == True:
                        similar_urls = GetSimilar(MAL_urls)
                        need_similar = CheckUrl(comment.body, similar_urls)
                        comment_reply = PrepareReply(anime_titles, MAL_urls, crunchy_urls, similar_urls, need_MAL, need_crunch, need_similar, parent_check)
                

def GetAnimeListHummingbird():
    url_list = ["http://hummingbird.me/anime/filter/newest?y[]=Upcoming&y[]=2010s&y[]=2000s&y[]=1990s&y[]=1980s&y[]=1970s&y[]=Older"]
    anime_title = []
    for url in url_list:
        req = urllib2.Request(url, headers={'User-Agent': "Anime Link Bot"})
        html_req = urllib2.urlopen(req)
        html_source = html_req.readlines()

        for line in html_source:
            if "<p class='title'>" in line:
                line = line.replace("<p class='title'>", "")
                line = line.replace("</p>", "")
                line = line.replace("\n", "")
                if line not in anime_title:
                    anime_title.append(line)
                    print line
            if "rel=\"next\">Next" in line:
                anime_link = line.split("\"")[1]
                anime_url = ("http://hummingbird.me" + anime_link)
                if anime_url not in url_list:
                    url_list.append(anime_url)
                    
## Waiting on MAL API Whitelist acceptance
def GetAnimeListMAL():
    url_list = ["http://myanimelist.net/anime.php?o=9&c[]=a&c[]=d&cv=2&w=1"]
    anime_title = []
    for url in url_list:
        req = urllib2.Request(url, headers={'User-Agent': ""})
        html_req = urllib2.urlopen(req)
        html_source = html_req.readlines()

        for line in html_source:
            print line
