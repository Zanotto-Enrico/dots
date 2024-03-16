if status is-interactive
    # Commands to run in interactive sessions can go here
	alias tmux='tmux -u'
	alias eduroam="$HOME/scripts/eduroam.sh"
	alias nmtui="$HOME/scripts/nmtui.sh"
    alias matrix="unimatrix -lp -s 95"
end

set -U fish_greeting 
