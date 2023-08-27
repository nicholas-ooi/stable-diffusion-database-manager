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
import re
import os
import json
import logging
from neo4j import GraphDatabase
import ipfshttpclient
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jDatabase:

    name = "Neo4j"
    driver = None
    session_instance = None
    components = None

    header = gr.Label(label=name, value=name, visible=False)
    connection_string = gr.Textbox(label="Connection String", visible=False, placeholder="bolt://localhost:7687")
    user_name = gr.Textbox(label="Username", visible=False, placeholder="neo4j")
    password = gr.Textbox(label="Password", visible=False, placeholder="Provide your password", type="password")
    connection_result_textarea = gr.TextArea(interactive=False, label='Connection Result', visible=False)
    test_button = gr.Button(value="Test Connection", visible=False)

    def __init__(self):
        self.bind_event_handlers()
        self.components = [
            self.header,
            self.connection_string,
            self.user_name,
            self.password,
            self.connection_result_textarea,
            self.test_button
        ]

    def bind_event_handlers(self):
        self.test_button.click(fn=self.test_connectivity, inputs=[self.connection_string, self.user_name, self.password], outputs=[self.connection_result_textarea])

    def instance(self, connection_string, user, password):
        self.driver = GraphDatabase.driver(connection_string, auth=(user, password))
        self.session_instance = self.driver.session()

    def test_connectivity(self, connection_string, user, password):
        message = ""
        try:
            self.instance(connection_string, user, password)
            self.session_instance.run("RETURN 1 AS connectivity_test")
            message = f"Connected successfully to {self.name}!\n"
        except Exception as e:
            message = f"Error connecting to {self.name}: {str(e)}"
        finally:
            self.close()
            return message

    def insert(self, processed, input_values):
        
        connection_string, user, password = input_values[1:4]
        self.instance(connection_string, user, password)

        try:
            with ipfshttpclient.connect() as client:
                for i in range(len(processed.images)):
                    regex = r"Steps:.*$"
                    info = re.findall(regex, processed.info, re.M)[0]
                    input_dict = dict(item.split(": ") for item in str(info).split(", "))

                    details = {
                        "seed": processed.seed,
                        "prompt": processed.prompt,
                        "neg_prompt": processed.negative_prompt,
                        "steps": int(input_dict["Steps"]),
                        "seed": int(input_dict["Seed"]),
                        "sampler": input_dict["Sampler"],
                        "cfg_scale": float(input_dict["CFG scale"]),
                        "size": tuple(map(int, input_dict["Size"].split("x"))),
                        "model_hash": input_dict["Model hash"],
                        "model": input_dict["Model"]
                    }

                    metadata = json.dumps(details)

                    image = processed.images[i]
                    
                    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    image.save(temp_file, 'PNG')
                    
                    response = client.add(temp_file.name)
                    ipfs_hash = response['Hash']

                    cypher_query = """
                    MERGE (p:Prompt {content: $prompt_content})
                    CREATE (image:Image {metadata: $metadata, ipfs_hash: $ipfs_hash})
                    MERGE (p)-[:RELATED_TO]->(image)
                    RETURN image
                    """
                    
                    self.session_instance.run(
                        cypher_query,
                        prompt_content=processed.prompt,
                        metadata=metadata,
                        ipfs_hash=ipfs_hash
                    )

            self.close()
        except Exception as e:
            print(f"Error inserting of data: {e}")
        finally:
            temp_file.close()
            os.remove(temp_file.name)


    def close(self):
        if self.session_instance:
            self.session_instance.close()
        if self.driver:
            self.driver.close()