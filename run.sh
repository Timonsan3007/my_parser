#!/bin/bash
source venv/bin/activate
python parser.py
python vk_parser.py
python tg_parser.py
python bot_sender.py
chmod +x run.sh
