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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from modules import generation_parameters_copypaste

class MongoDBDatabase:

    name = "MongoDB"
    client = None
    database = None
    components = None

    header = gr.Label(label=name, value=name, visible=False)
    connection_string = gr.Textbox(label="Connection String", visible=False, placeholder="mongodb://root:your_password@localhost:27017/")
    database_name = gr.Textbox(label="Database Name", visible=False, placeholder="Provide the name of the database")
    collection_name = gr.Textbox(label="Collection Name", visible=False, placeholder="Provide the name of the collection")
    connection_result_textarea = gr.TextArea(interactive=False, label='Connection Result', visible=False)
    test_button = gr.Button(value="Test Connection", visible=False)

    def __init__(self):
        self.bind_event_handlers()
        self.components = [
            self.header,
            self.connection_string,
            self.database_name,
            self.collection_name,
            self.connection_result_textarea,
            self.test_button
        ]

    def bind_event_handlers(self):
        self.test_button.click(fn=self.test_connectivity, inputs=[self.connection_string], outputs=[self.connection_result_textarea])

    def instance(self, connection_string, db_name):
        self.client = MongoClient(connection_string)
        self.database = self.client[db_name]

    def test_connectivity(self, connection_string):
        message = ""
        try:
            self.instance(connection_string, "test_db")
            self.database.command("ping")
            message = f"Connected successfully to {self.name}!\n"
        except Exception as e:
            message = f"Error connecting to {self.name}: {str(e)}"
        finally:
            self.close()
            return message

    def insert(self, processed, input_values):

        connection_string, db_name, collection_name = input_values[1:4]

        self.instance(connection_string, db_name)
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
