This repo is examples of webcrawlers built using the Scrapy python framework.  For more details about Scrapy..

 - [Scrapy Framework](https://github.com/scrapy/scrapy/)
 - [Wiki](https://github.com/scrapy/scrapy/wiki)

Scrapy-Spiders (functional examples)
====================================

Collection of python scripts I have created to crawl various websites, mostly for 
lead generation projects to match keywords and collect email addresses and post URLs.

Each script is organized within it's own folder and then combined into a single run 
script within the 'dist' folder.

Contribute
----------
If you create a new crawler, please add it to the repo and send me a pull request.  I'd like to build this up as a collection beyond just these few I wrote myself.

Spiders
-------

# Functionality

* Specify keywords
* Specify all time (by leaving null) or specific date
* Specify specific category (ie Gigs, Jobs, For Sale, etc..) or full site (by leaving null).
* Bot crawls all of Craigslist (worldwide, all domains) searching for posts posted on the specified timeperiod which match any of the specified keywords.  All matches trigger the bot to search for any email addresses written within the post body, as well as the reply email address, the email address is recorded to a txt file in CSV format.

# Sites

* subdomain.Craigslist.org
* Mandy.com
* ProductionHub.com
* EntertainmentCareers.net
* NewEnglandFilm.com
* Reel-scout.com

About Scrapy
------------

Scrapy is a fast high-level screen scraping and web crawling framework, used to crawl 
websites and extract structured data from their pages. It can be used for a wide range 
of purposes, from data mining to monitoring and automated testing.

ref: http://www.scrapy.org

Setup Guide
-----------

// Remove previous installation of Python 2.7
sudo rm -R /System/Library/Frameworks/Python.framework/Versions/2.7

// Install Homebrew
$ ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"

// Add to profile
~/.bashrc
export PATH=/usr/local/bin:/usr/local/sbin:$PATH

// Fresh install Python 2.7
brew install python

// Add to profile
~/.bashrc
export PATH=/usr/local/share/python:$PATH

// Install Scrapy library with pip (pip should have been installed by brew when you installed python)
pip install Scrapy

// Setup project directory wherever you want (I just put it on my desktop)
sudo mkdir ~/Desktop/ProjectName
cd ~/Desktop/ProjectName

//Setup individual spider projects
scrapy startproject spiderOne
scrapy startproject spiderTwo
scrapy startproject spiderThree

//To run each spider individually
cd ~/Desktop/ProjectName
cd spiderOne
scrapy crawl spiderOne

etc..

!!WARNING!!
===========
You should not scrape any website that you do not own unless you have gotten consent from the 
webmaster of the site.  Using these scripts, can and will cause you to be blacklisted if used 
abusively and/or incorrectly.  This repository is for reference purposes only and should not be
run on a live environment.
