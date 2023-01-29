#!/usr/bin/env python3
import argparse
import logging
import sys
import signal
import gi
import json
import time
import threading  
gi.require_version('Playerctl', '2.0')
from gi.repository import Playerctl, GLib

logger = logging.getLogger(__name__)
status = 'playing'
offset = 0
SavedText = ""
SavedPlayer = None

def write_output(text, player):
    logger.info('Writing output')
    
    global SavedText, SavedPlayer
    if(text != ""):
        SavedText = text + " - "
    SavedPlayer = player

def update_output():
    while True:
        if(SavedPlayer != None and SavedText != ""):
            output = {'text': move_text(SavedText)[:20],
                        'class': 'custom-' + SavedPlayer.props.player_name,
                        #'alt': player.props.player_name}
                        'alt': status}
            sys.stdout.write(json.dumps(output) + '\n')
            sys.stdout.flush()
        else:
            sys.stdout.write(json.dumps({'text': 'Nessun Brano        ','alt':'paused'}) + '\n')
            sys.stdout.flush()
            
        time.sleep(0.2)
    

def move_text(text):
    global offset
    if( len(text) <= 20):
        return text
    offset = (offset+1)%len(text)
    newText = ""
    for i in range(offset,len(text)):
        newText = newText+text[i]
    for i in range(0, offset):
        newText = newText + text[i]
    return newText


def on_play(player, status, manager):
    logger.info('Received new playback status')
    on_metadata(player, player.props.metadata, manager)


def on_metadata(player, metadata, manager):
    logger.info('Received new metadata')
    track_info = ''

    if player.props.player_name == 'spotify' and \
            'mpris:trackid' in metadata.keys() and \
            ':ad:' in player.props.metadata['mpris:trackid']:
        track_info = 'AD PLAYING'
    elif player.get_artist() != None and player.get_title() != None:
        track_info = '{artist} - {title}'.format(artist=player.get_artist(),
                                                 title=player.get_title())
    else:
        track_info = player.get_title()
    global status
    if player.props.status != 'Playing' and track_info:
        status = 'paused'
    else:
        status = 'playing'
    write_output(track_info, player)


def on_player_appeared(manager, player, selected_player=None):
    if player is not None and (selected_player is None or player.name == selected_player):
        init_player(manager, player)
    else:
        logger.debug("New player appeared, but it's not the selected player, skipping")


def on_player_vanished(manager, player):
    logger.info('Player has vanished')
    sys.stdout.write('\n')
    sys.stdout.flush()
    global SavedPlayer
    SavedPlayer = None


def init_player(manager, name):
    logger.debug('Initialize player: {player}'.format(player=name.name))
    player = Playerctl.Player.new_from_name(name)
    player.connect('playback-status', on_play, manager)
    player.connect('metadata', on_metadata, manager)
    manager.manage_player(player)
    on_metadata(player, player.props.metadata, manager)


def signal_handler(sig, frame):
    logger.debug('Received signal to stop, exiting')
    sys.stdout.write('\n')
    sys.stdout.flush()
    # loop.quit()
    sys.exit(0)


def parse_arguments():
    parser = argparse.ArgumentParser()

    # Increase verbosity with every occurrence of -v
    parser.add_argument('-v', '--verbose', action='count', default=0)

    # Define for which player we're listening
    parser.add_argument('--player')

    return parser.parse_args()


def main():
    arguments = parse_arguments()

    # Initialize logging
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                        format='%(name)s %(levelname)s %(message)s')

    # Logging is set by default to WARN and higher.
    # With every occurrence of -v it's lowered by one
    logger.setLevel(max((3 - arguments.verbose) * 10, 0))

    # Log the sent command line arguments
    logger.debug('Arguments received {}'.format(vars(arguments)))

    manager = Playerctl.PlayerManager()
    loop = GLib.MainLoop()

    manager.connect('name-appeared', lambda *args: on_player_appeared(*args, arguments.player))
    manager.connect('player-vanished', on_player_vanished)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    for player in manager.props.player_names:
        if arguments.player is not None and arguments.player != player.name:
            logger.debug('{player} is not the filtered player, skipping it'
                         .format(player=player.name)
                         )
            continue

        init_player(manager, player)
    th1 = threading.Thread(target=update_output, args=())  
    th1.start()
    loop.run()

if __name__ == '__main__':
    main()
