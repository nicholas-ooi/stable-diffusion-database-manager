"""
MIT License

Copyright (c) [2023] Nicholas Ooi
https://github.com/nicholas-ooi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import gradio as gr
from pymongo import MongoClient
from io import BytesIO
import logging
from modules import generation_parameters_copypaste
from modules import shared
from .setting_button import OptionButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBDatabase:

    name = "MongoDB"
    client = None
    database = None
    components = None

    def __init__(self):
        shared.options_templates.update(
            shared.options_section(
                ('nex-databases', "Nex databases"), {
                    f'nex_databases_enable_mongodb': shared.OptionInfo(False, 'Enable MongoDB'),
                    f'nex_databases_connection_string_mongodb': shared.OptionInfo(
                        "", 'Connection String - MongoDB', gr.Textbox,
                        {'placeholder': 'mongodb://root:your_password@localhost:27017/'}
                    ),
                    f'nex_databases_database_name_mongodb': shared.OptionInfo("", 'Database Name - MongoDB'),
                    f'nex_databases_collection_name_mongodb': shared.OptionInfo("", 'Collection Name - MongoDB'),
                    f'nex_databases_test_button_mongodb': OptionButton('Test - MongoDB!', self.test_connectivity),
                }
            )
        )

    def instance(self):
        self.client = MongoClient(shared.opts.nex_databases_connection_string_mongodb)
        self.database = self.client[shared.opts.nex_databases_database_name_mongodb]

    def test_connectivity(self):
        try:
            self.instance()
            self.database.command("ping")
            message = f"Connected successfully to {self.name}!"
            gr.Info(message)
        except Exception as e:
            message = f"Error connecting to {self.name}: {str(e)}"
            gr.Warning(message)
        finally:
            self.close()

    def insert(self, processed):
        if not shared.opts.nex_databases_enable_mongodb:
            return

        collection_name = shared.opts.nex_databases_collection_name_mongodb
        self.instance()
        collection = self.database[collection_name]

        for i in range(len(processed.images)):
            
            image = processed.images[i]
            buffer = BytesIO()
            image.save(buffer, "png")
            image_bytes = buffer.getvalue()

            data = {
                "metadata": generation_parameters_copypaste.parse_generation_parameters(processed.infotexts[i]),
                "image": image_bytes
            }

            try:
                collection.insert_one(data)
            except Exception as e:
                logger.error(f"Error inserting data: {e}")
                raise e
            
        self.close()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
