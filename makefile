.PHONY: start-vnc-debug kill-vnc-debug fresh-vnc-debug hsbc-download show-mouse

include .env
export

help: ## Display this screen
	@echo "Usage: make [target]"
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s \033[0m %s\n", $$1, $$2}'

start-vnc-debug: ## Starts a VNC session for debugging.
	- touch ~/.Xauthority
	2>/dev/null 1>&2 Xvfb :99 -screen 0 1920x1080x24 &
	sleep 1
	2>/dev/null 1>&2 x11vnc -display :99 -localhost -forever -passwd mysecret &
	sleep 1
	export DISPLAY=:99; 2>/dev/null 1>&2 firefox --width 1800 --height 900 "https://www.hsbc.com.au" &  


kill-vnc-debug: ## Cleans up old processes spawned with VNC
	-	pkill firefox
	- pkill x11vnc
	- pkill Xvfb
	- rm ~/.Xauthority

fresh-vnc-debug: kill-vnc-debug start-vnc-debug ## Kills old VNC instances and creates new ones.

hsbc-download: ## Runs pyautogui clicker for HSBC downloads
	export DISPLAY=:99; python3 bank-statements/hsbc.py 

show-mouse: ## View current mouse coordinates
	export DISPLAY=:99; python3 -c "import pyautogui; pyautogui.displayMousePosition()" 

