import configparser
import os
import codecs
import sys
import argparse
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from _socket import timeout
import time
import json
import glob
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--directory", help="directory to edit metadata for")
parser.add_argument("-l", "--library", help="library of directories to edit metadata for")
parser.add_argument("-f", "--force", action="store_true", help="force scan the directories.")
args = parser.parse_args()
force = args.force

if args.directory and os.path.split(args.directory)[1] == '':
    args.directory = os.path.split(args.directory)[0]

if args.library and os.path.split(args.library)[1] == '':
    args.library = os.path.split(args.library)[0]

if not args.library and not args.directory:
    print('no library or directory specified')
    sys.exit()


config_file = 'config.cfg'

with codecs.open(os.path.join(os.path.split(os.path.realpath(__file__))[0], config_file), 'r', "utf8") \
        as config_open_file:
    conf = configparser.ConfigParser()
    conf.read_file(config_open_file)


api_key = conf.get('SETTINGS', 'tmdb_api_key')
main_language = conf.get('SETTINGS', 'main_language')
secondary_language = conf.get('SETTINGS', 'secondary_language')
fields_to_change = conf.get('SETTINGS', 'fields_to_change').lower().split(',')

if len(api_key) != 32:
    print('no functional api key provided')

tmdb_id = None
main_tmdb_details = None
sec_tmdb_details = None


def modify_tag(xml_dict, tag, new_string):

    count = 0
    for line in xml_dict:
        if '<' + tag.lower() + '>' in line.lower():
            xml_dict[count] = '  <' + tag.lower() + '>' + new_string + '</' + tag.lower() + '>'
            break
        count += 1


def get_tmdb_details_data(lang):
    global tmdb_id
    response = retrieve_web_page('https://api.themoviedb.org/3/movie/'
                                 + tmdb_id +
                                 '?api_key=' + api_key +
                                 '&language=' + lang, 'movie details')
    if response is None:
        return None
    data = json.loads(response.read().decode('utf-8'))
    response.close()

    return data


def retrieve_web_page(url, page_name='page'):

    response = None
    print('Downloading ' + page_name + '.')

    for tries in range(1, 10):
        try:
            response = urlopen(url, timeout=2)
            break

        except UnicodeEncodeError as e:
            print('Failed to download ' + page_name + ' : ' + str(e) + '. Skipping.')
            break

        except timeout:
            if tries > 5:
                print('You might have lost internet connection.')
                break

            time.sleep(1)
            print('Failed to download ' + page_name + ' : timed out. Retrying.')

        except HTTPError as e:
            print('Failed to download ' + page_name + ' : ' + str(e) + '. Skipping.')
            break

        except URLError:
            if tries > 3:
                print('You might have lost internet connection.')
                raise

            time.sleep(1)
            print('Failed to download ' + page_name + '. Retrying.')

    return response


def get_imdb_content_rating():
    response = retrieve_web_page("https://www.imdb.com/title/" + imdb_id +
                                 "/parentalguide?ref_=tt_ql_stry_5", 'certification page on imdb')
    data = response.read()
    response.close()
    soup = BeautifulSoup(data, features="html.parser")
    cert = str(soup.findAll("a", {"href": lambda l: l and l.startswith('/search/title?certificates=' +
                                                                       main_language[-2:] + ':')}))
    try:
        cert = cert.split(':')[1].split('"')[0]
    except IndexError:
        print('The movie "' + movie_directory + '" don\'t have a content rating on imdb for this country.')
        cert = '???'

    return cert


def handle_movie():
    global tmdb_id
    global imdb_id
    global main_tmdb_details
    global sec_tmdb_details
    nfo_path = None
    nfo_string = None
    for filename in glob.glob(os.path.join(movie_directory, '*.nfo')):
        with codecs.open(filename, 'r', 'utf-8') as file:
            nfo_string = file.read()
        nfo_path = filename

    if not nfo_string:
        print('something went wrong! (123)')

    nfo = nfo_string.split('\n')
    print('working on: "' + nfo_path + '".')

    for line in nfo:
        if '<tmdbid>' in line:
            tmdb_id = line.replace('<tmdbid>', '').replace('</tmdbid>', '').strip()
            break
    for line in nfo:
        if '<imdbid>' in line:
            imdb_id = line.replace('<imdbid>', '').replace('</imdbid>', '').strip()
            break
    locked_fields = ""
    for line in nfo:
        if '<lockedfields>' in line:
            locked_fields = line.replace('<lockedfields>', '').replace('</lockedfields>', '').strip()
            break

    for field in fields_to_change:

        if field.strip() == 'summary':
            if not force:
                if 'overview' in locked_fields.lower():
                    continue
            if not main_tmdb_details:
                main_tmdb_details = get_tmdb_details_data(main_language)
                if not main_tmdb_details:
                    continue
            modify_tag(nfo, 'plot', main_tmdb_details['overview'])
            if 'Overview' not in locked_fields:
                locked_fields += '|Overview'

        elif field.strip() == 'genres':
            if not force:
                if 'genres' in locked_fields.lower():
                    continue
            count = 0
            for line in nfo:
                if '<genre>' in line:
                    for change_to, change_from_string in conf.items('GENRES'):
                        change_from_list = change_from_string.split(',')
                        for change_from in change_from_list:
                            tmp = line.replace('<genre>', '').replace('</genre>', '').lower().strip()
                            tmp2 = change_from.lower().strip()
                            if tmp == tmp2:
                                nfo[count] = '  <genre>' + change_to.lower().title() + '</genre>'
                count += 1
            if 'Genres' not in locked_fields:
                locked_fields += '|Genres'

        elif field.strip() == 'content_rating':
            if not force:
                if 'officialrating' in locked_fields.lower():
                    continue
            content_rating = get_imdb_content_rating()
            found = False
            for line in nfo:
                if '<mpaa>' in line:
                    for change_to, change_from_string in conf.items('RATINGS'):
                        change_from_list = change_from_string.split(',')
                        for change_from in change_from_list:
                            tmp = content_rating.lower().strip()
                            tmp2 = change_from.lower().strip()
                            if tmp == tmp2:
                                content_rating = change_to.lower().strip().upper()
                                found = True
                                break
            if not found:
                content_rating = '???'

            modify_tag(nfo, 'mpaa', content_rating)
            if 'OfficialRating' not in locked_fields:
                locked_fields += '|OfficialRating'

        elif field.strip() == 'original_title_mod':
            if not force:
                if 'title' in locked_fields.lower():
                    continue
            if not main_tmdb_details:
                main_tmdb_details = get_tmdb_details_data(main_language)
                if not main_tmdb_details:
                    continue
            if not sec_tmdb_details:
                sec_tmdb_details = get_tmdb_details_data(secondary_language)
                if not sec_tmdb_details:
                    continue

            if main_tmdb_details['title'] == main_tmdb_details['original_title']:
                new_title = main_tmdb_details['title']
                new_otitle = main_tmdb_details['title']
                if main_tmdb_details['title'] != sec_tmdb_details['title']:
                    new_otitle += ' :: ' + sec_tmdb_details['title']
            elif sec_tmdb_details['title'] == sec_tmdb_details['original_title']:
                new_title = sec_tmdb_details['title']
                new_otitle = sec_tmdb_details['title']
                if main_tmdb_details['title'] != sec_tmdb_details['title']:
                    new_otitle += ' :: ' + main_tmdb_details['title']
            else:
                new_title = sec_tmdb_details['title']
                new_otitle = sec_tmdb_details['original_title'] + ' :: ' + sec_tmdb_details['title']
                if main_tmdb_details['title'] != sec_tmdb_details['title']:
                    new_otitle += ' :: ' + main_tmdb_details['title']
            modify_tag(nfo, 'originaltitle', new_otitle)
            modify_tag(nfo, 'title', new_title)
            modify_tag(nfo, 'lockdata', 'true')
            if 'Title' not in locked_fields:
                locked_fields += '|Title'



    count = 0
    for line in nfo:
        if '<lockedfields>' in line:
            nfo.pop(count)
            break
        count += 1

    if len(locked_fields) > 0:
        if locked_fields.startswith('|'):
            locked_fields = locked_fields[1:]
        count = 0
        for line in nfo:
            if '<lockdata>' in line:
                nfo[count] += '\n  <lockedfields>' + locked_fields + '</lockedfields>'
            count += 1

    nfo = '\n'.join(nfo)

    with codecs.open(nfo_path, 'w', 'utf-8') as file:
        file.write(nfo)
    print('done')


if args.directory:
    movie_directory = args.directory
    handle_movie()
else:
    for movie in os.listdir(args.library):
        movie_directory = os.path.join(args.library, movie)
        handle_movie()

sys.exit()
