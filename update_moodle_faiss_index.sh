#!/bin/zsh
# This script retrieves course data from your Moodle instance
# You should have a directory `prujuai_moodle`` with a subdirectory `faiss_index`
# The directory `prujuai_moodle`` should be course defined as `CHAT_DATA_FOLDER`
# Launches gradio app when done
python3 moodle.py
cp moodle_data_vdb/index.faiss prujuai_moodle/faiss_index/
cp moodle_data_vdb/index.pkl prujuai_moodle/faiss_index/
gradio app.py

