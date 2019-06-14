#!/usr/bin/env python3

# Python script for downloading subtitles from https://subscene.com
# Copyright : Vikas Chouhan (presentisgood@gmail.com)
# License   : GPLv2
#
# Dependencies : unrar should be installed
#                rarfile (python module) is required

from   bs4 import BeautifulSoup
import requests
import itertools
import re
import os, sys
import zipfile
import io
import argparse
try:
  import rarfile
except:
  print("rarfile should be installed.")
  sys.exit(-1)
# entry

# User-agent
headers = {'User-Agent' : "Mozilla/5.0"}

# mkdir -p (after checking if it already exists)
def make_dirs(dir_path):
    # Create dir_path if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    # endif
# enddef

# Main function
def fetch_subs(proxy):
    out_dir   = os.path.expanduser('~') + '/subs/'    # Target directory
    url_home  = 'https://subscene.com'
    cntr      = 0;

    # Get cookies
    sess      = requests.Session()
    res       = sess.get(url_home, headers=headers, proxies=proxy)
    cookies   = dict(res.cookies)

    s_str     = str(input('Enter movie name (if your term yields no results, append year also with a space): '))
    s_filter  = str(input('Enter a pattern to filter (Just hit Enter to ignore) : '))
    org_title = s_str

    # NOTE:
    # As of 6th June 2019, from what I tested subscene.com has removed their API
    # based search page. It's now javascript driven. I don't have time or energy
    # to implement it. Thus the use directly has to provide title name not a search term,

    # Modify movie title
    s_tokens  = s_str.lower().split()

    # Get title and url
    link_title  = s_str
    all_cat_l   = list(itertools.combinations_with_replacement(['-', ''], len(s_tokens)-1))
    all_cat_l   = list(set(all_cat_l).union(set([x[::-1] for x in all_cat_l])))

    assert len(all_cat_l[0]) == len(s_tokens) - 1, 'This should never happen !!'
    match_found = False

    for cat_l_t in all_cat_l:
        link_title = ''
        item_ctr   = 0
        for delim_t in cat_l_t:
            link_title += s_tokens[item_ctr] + delim_t
            item_ctr += 1
        # endfor
        link_title += s_tokens[item_ctr]
        url_this    = url_home + '/subtitles/{}'.format(link_title)
        print("Trying {}".format(url_this))

        # Refresh new cookies for each url search cookies
        sess      = requests.Session()
        res       = sess.get(url_this, headers=headers, proxies=proxy)
        cookies   = dict(res.cookies)

        req_this   = sess.get(url_this, cookies=cookies)
        if req_this.status_code == 200:
            page_this   = req_this.text
            match_found = True
            break
        else:
            print('Fetching {} returned status code {}'.format(url_this, req_this.status_code))
        # endif
    # endfor

    if match_found == False:
        print('Title "{}" not found. This is no search engine !! Please spell correctly or try after some time if encountered 409 errors.'.format(org_title))
        sys.exit(-1)
    # endif

    soup_this   = BeautifulSoup(page_this, 'lxml')
    hrefs2_list = soup_this.find_all('a', href=re.compile(r'\/subtitles\/{}\/'.format(link_title)))
    print("Found {} subtitles in all languages.".format(len(hrefs2_list)))

    main_lang   = u'English'
    title_list  = []

    for indx in range(0, len(hrefs2_list)):
        span_list = hrefs2_list[indx].find_all('span')
        lang_this = span_list[0].text.replace('\t', '').replace('\n', '').replace('\r', '')
        mov_name  = span_list[1].text.replace('\t', '').replace('\n', '').replace('\r', '')

        # Filter links
        if s_filter != None and s_filter != '':
            if bool(re.search(s_filter, mov_name)) == False:
                continue
            # endif
        # endif

        if lang_this == main_lang:
            title_list.append({
                                   'lang'   : lang_this,
                                   'title'  : mov_name,
                                   'href'   : hrefs2_list[indx],
                             })
        # endif
    # endfor

    print("Found {} {} subtitles.".format(len(title_list), main_lang))
    if len(title_list) == 0:               # if no list was returned, just return
        return
    # endif

    print("Downloading all {} subtitles.".format(main_lang))

    # Create out_dir if it doesn't exist
    make_dirs(out_dir)

    for item in title_list:
        url_this    = url_home + item['href']['href']
        req_this    = sess.get(url_this, cookies=cookies)
        if req_this.status_code != 200:
            print('Fetching {} returned status code {}'.format(url_this, req_this.status_code))
            continue
        # endif

        soup_this   = BeautifulSoup(req_this.text, 'lxml')
        down_btn    = soup_this.find('div', { 'class' : 'download'})   # Get download button
        if down_btn == None:
            continue
        # endif
        btn_href    = down_btn.find('a')['href']
        url_next    = url_home + btn_href

        req_this    = sess.get(url_next, cookies=cookies)
        if req_this.status_code != 200:
            print('Fetching {} returned status code {}'.format(url_next, req_this.status_code))
            continue
        # endif
        file_fp     = io.BytesIO(req_this.content)
        m_title     = item['title'].encode('utf-8')
        tgt_dir     = '{}/{}'.format(out_dir, m_title)
        try:
            try:
                with zipfile.ZipFile(file_fp, "r") as zfp:
                    print("Extracting {} in {}".format(m_title, tgt_dir))
                    make_dirs(tgt_dir)
                    zfp.extractall(tgt_dir)
                # endwith
            except zipfile.BadZipfile:
                with rarfile.RarFile(file_fp, "r") as rfp:
                    print("Extracting {} in {}".format(m_title, tgt_dir))
                    make_dirs(tgt_dir)
                    rfp.extractall(tgt_dir)
                # endwith
            # endtry
        except rarfile.RarUnknownError or rarfile.BadRarFile:
            print("Warning: Not a valid zip or rar file. Writing as it is.".format(url_next))
            with open('{}/{}.{}'.format(out_dir, cntr, 'unknown'), 'w') as fp:
                fp.write(file_fp.getvalue())
            # endwith
            cntr = cntr + 1
    # endfor
# enddef

if __name__ == '__main__':
    parser     = argparse.ArgumentParser()
    parser.add_argument('--use_onion', help='Use onion website.', action='store_true')
    args       = parser.parse_args()
    use_onion  = args.__dict__['use_onion']
    proxy      = {}

    if use_onion:
       proxy   = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
    # endif

    fetch_subs(proxy)
# endif
