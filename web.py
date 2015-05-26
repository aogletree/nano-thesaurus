"""
Web Scraper 

This is a module that visits a fairly specific website, downloads all the paper abstracts it finds, and outputs a file 
with the word count of all meaningful words.

TODO: This can also be done in an object model
"""


import mechanize   #For the 
import operator    #For soring the word dictionary
import re          #For treating input tokens

def setup():
    """
    @function setup
    
    Performs all of the web browser setup without including it in the body code.

    @return a mechanize browser without the mess of setting it up
    """
    br = mechanize.Browser()
    #br.set_all_readonly(False)    # allow everything to be written to
    br.set_handle_robots(False)   # no robots
    br.set_handle_refresh(False)  # can sometimes hang without this
    br.addheaders = [('User-agent', 'Firefox (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    # [('User-agent', 'Firefox')]
    return br


def getAbstractList(b):
    """
    @function getAbstractList
    Takes an input browser and navigates it to all of the links that look like an abstract, and navigates to them, pulls the abstract out, and navigates back
    @param b A Mechanize browser
    @return Returns a list of links, texts and abstracts
    TODO: Put the interior list into a tuple
    """
    print "\tGetting Abstracts From: ",b.geturl() 
    browser = b
    output_list=[]
    link_list = [link for link in browser.links()]

    for link in link_list:
        if("arXiv:" in link.text):
            #print link.text, link.url
            request = browser.click_link(link)
            print "\t\tFollowing Link: ", link.text, " : ", link.url
            response = browser.follow_link(link)
            print "\t\t",response.geturl()
            str_response = response.read().split("<span class=\"descriptor\">Abstract:</span> ")[1].split("</blockquote>")[0]
            output_list.append([link.text,link.url, str_response] )
            b.back()
    return output_list

def NavigateNext(b):
    """
    @function NavigateNext
    Navigates a mechanize browser to the next batch of results (if possible) returns success
    @param b A Mechanize Browser
    @return bool if the browser can navigate to the next batch of results
    """
    for link in b.links():
        if "Next" in link.text and "results" in link.text:
            request = b.click_link(link)
            print "Navigating to Link: ", link.text, " : ", link.url
            response = b.follow_link(link)
            return True


def eliminate_words(in_list):
    """
    @function eliminate_words
    Using the ignore list, eliminates stop words for an input word list
    @param in_list A list of words
    @param out An output list of words sans ignored words
    """
    ignore_list=['_', 'a', 'an', 'and', 'also', 'are', 'as', 'at', 'be', 'been', 'by', 'for', 'from', 'has', 'in', 'is', 'it', 'of', 'on', 'or', 'our', 'that', 'the', 'their', 'these', 'this', 'to', 'using', 'was', 'we', 'were', 'which', 'with']
    out = []
    for x in in_list:
        is_not_ignored = True
    for y in ignore_list:
        if(x==y):
            is_not_ignored = False
        if(is_not_ignored):
            out.append(x)
    return out

def main():
    """
    @function main
    See module doc. This is a mess
    """
    br = setup()
    response = br.open("http://arxiv.org/find/all/1/all:+nanocrystalline/0/1/0/all/0/1")

    #Do the initial navigating
    print "Navigating to : ", br.geturl()
    output_list=getAbstractList(br)

    #now navigate to the other links
    while( NavigateNext(br) ):
        little_list = getAbstractList(br)
        for i in little_list:
            output_list.append(i)

    #Create a dictionary of {word, word_count}
    word_dict={}
    for i in output_list:
        
        #This gets the abstract out of each entry
        ab = i[2]
        
        #Strips the whitespace off 
        #TODO: This also needs to be modified to do punctuation
        word_list = re.findall(r"[\w']+", ab)
        
        #Eliminate words. Seriously, this needs an object model
        word_list = eliminate_words(word_list)
        
        #Modify the dictionary, note that I use a try/except statement to test the dictionary for entries that may/may-not exist
        for word in word_list:
            lowercase = word.lower()
            try:
                #Update the count
                count = word_dict[lowercase]
                word_dict[lowercase] = count+1
            except KeyError as e:
                #Create a new dictionary entry
                word_dict[lowercase]=1
    
    #Sort the dictionary
    sorted_dict = sorted(word_dict.items(), key=operator.itemgetter(1))
    #print sorted_dict to file
    f = open('word_count.txt', 'w')
    for i in sorted_dict:
        f.write(str(i)+"\n")

if __name__ == "__main__":
    main()
