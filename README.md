# EME
A script for complementing the emby generated metadata nfo file. the reason why I made this script was because I wanted to 
have english metadata source but with a few individual metadata fields from Swedish. It's fairly limmited in scope and not a 
lot of configurable options, but adding functionallity to the script should be fairly easy so if you have any specific requests 
just open an issue.

it can work on 4 fields:

### Summary

when this field is enabled it'll download a summary of the movie in your main language but will fallback to your secondary 
language if it didn't find any summary on tmdb site.

### content rating. 

I've made a webcrawler that will find the content rating for your main country on IMDB since they are a better source of content 
rating in non-US countries, if it can't find one it will give the movie a content rating of "???". it can also transform these ratings.

### genre renaming. 

this change won't actually look up any metadata. it'll simply translate/change the genres for your movies according to how 
you've configured it.

### original title and title

this is changing the way the original title field is used. It will use this field to list original title along side with the titles 
of the movie in your main and secondary language like so: <original title> :: <secondary language title> :: <main language title>. 
  it won't list any duplicates.
  
this "mod" is made in order to enable searching for movies in multiple languages. so if you have this mod enabled you can have 
titles in english but still search for movies in your main language (swedish for example). this work since emby also searches 
for string matches in the original title field.

### locking data
whenever a field have been edited by the script it will automatically lock that field so that it won't get changed back by a library
metadata refresh. maybe I'll add this as a option down the road but for now this is part of the script. note that the original_title
can't be locked so will therefore lock the entire movie from changing anything in the nfo file autmatically.

## INSTALLATION

clone the repository and install the bs4 module. you'll also need to add a config.cfg file. you can use the config-template.cfg file as
a template. edit it and rename it to config.cfg. then run the script with python3. it expects a -l or an -d flag followed by a library
directory to your movies or a directory path to a movie folder. 
