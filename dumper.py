import ConfigParser
import getopt
import json
import os
import requests
import sys
import time


# Returns login response's cookies
def log_in(username, password):
    print "Preparing to take a dump by logging in..."

    login_data = { "type": "login", "alias": username, "password": password }
    login_resp = requests.post("http://np.ironhelmet.com/arequest/login", data=login_data)

    if login_resp.status_code != 200 or not login_resp.cookies:
        print "Failed to log in correctly. Check your credentials."
        sys.exit(1)

    print "Logged in!"
    return login_resp.cookies


# Returns the current game state as json
def get_game_state(cookies, game_number):
    print "Getting game state to dump..."

    get_state_data = { "type": "order", "order": "full_universe_report", "version": "7", "game_number": game_number }
    get_state_resp = requests.post("http://np.ironhelmet.com/grequest/order", data=get_state_data, cookies=cookies)

    if get_state_resp.status_code != 200:
        print "Failed to get game state. Bother Mohammed, but not until the game is over."
        sys.exit(1)

    print "Game state received!"
    return get_state_resp.text


def dump_file(state_json_str, game_number):
    state_json = json.loads(state_json_str)
    tick = state_json['report']['tick']
    player = state_json['report']['player_uid']

    filename = "gamestate_{0}_{1:02d}_{2:08d}.json".format(game_number, player, tick)
    print "Taking a dump on {}/{}...".format('dumps', filename)

    if not os.path.exists('dumps'):
        os.makedirs('dumps')

    with open('dumps/' + filename, 'w') as dump_file:
        dump_file.write(state_json_str)

    print "Finished taking dump."


def print_usage():
    script_name = sys.argv[0]
    print "Usage 1: python {0} [-c config_file.ini]".format(script_name)
    print "Note:    config file is an INI file and defaults to \"np2d-config.ini\" (which is generated by setup.py)"
    print "Usage 2: python {0} -u username -p password -g game_number [-t refresh_interval]".format(script_name)
    print "Note:    refresh interval is measured in seconds and defaults to 60"


def parse_args(args):
    dic = {}
    
    if (len(args) == 0):
        dic['config_file'] = 'np2d-config.ini'
        return dic
    
    opts = getopt.getopt(args, 'hc:u:p:g:t:')
    for o,a in opts[0]:
        if o == '-h':
            dic['help'] = True
            break
        elif o == '-c':
            dic['config_file'] = a
            break
        elif o == '-u':
            dic['username'] = a
        elif o == '-p':
            dic['password'] = a
        elif o == '-g':
            dic['game_number'] = a
        elif o == '-t':
            dic['refresh_interval'] = a
    
    return dic


def validate_args(dic):
    if 'help' in dic:
        print_usage()
        sys.exit(0)

    if 'config_file' in dic:
        config_filename = dic['config_file']
        if not os.path.exists(config_filename):
            print "Error: config file \"{0}\" not found".format(config_filename)
            print_usage()
            sys.exit(1)

        print "Reading config from \"{0}\"...".format(config_filename)
        config = ConfigParser.ConfigParser()
        config.read(config_filename)
        dic['username'] = config.get('config', 'username') or ''
        dic['password'] = config.get('config', 'password') or ''
        dic['game_number'] = config.get('config', 'game_number') or ''
        dic['refresh_interval'] = config.get('config', 'refresh_interval') or ''
    
    if 'username' not in dic or dic['username']=='':
        print "Error: username was not specified; exiting..."
        print_usage()
        sys.exit(1)
    
    if 'password' not in dic or dic['password']=='':
        print "Error: password was not specified; exiting..."
        print_usage()
        sys.exit(1)
    
    if 'game_number' not in dic or dic['game_number']=='':
        print "Error: game number was not specified; exiting..."
        print_usage()
        sys.exit(1)
    
    if 'refresh_interval' not in dic or dic['refresh_interval']=='':
        dri = 60 # default refresh interval
        dic['refresh_interval'] = dri
        print "Info:  refresh interval was not specified; defaulting to {0} seconds...".format(dri)


def main():
    args = [] if len(sys.argv)==1 else sys.argv[1:]
    dic = parse_args(args)
    validate_args(dic)

    cookies = log_in(dic['username'], dic['password'])
    refresh_interval = dic['refresh_interval']

    while True:
        state = get_game_state(cookies, dic['game_number'])
        dump_file(state, dic['game_number'])

        print "Waiting {0} seconds until next bowel movement...".format(refresh_interval)
        time.sleep(float(refresh_interval))


if __name__ == '__main__':
    main()

