#!/bin/bash

SESSION="system_monitor"

tmux new-session -d -s $SESSION

tmux split-window -v -t $SESSION
tmux split-window -v -t $SESSION

tmux select-pane -t $SESSION:0.0
tmux split-window -v -t $SESSION

tmux send-keys -t $SESSION:0.0 'tail -f bot.log' C-m
tmux send-keys -t $SESSION:0.1 'tail -f uvicorn.log' C-m
tmux send-keys -t $SESSION:0.3 'nvtop' C-m

tmux select-pane -t $SESSION:0.2

tmux attach -t $SESSION
