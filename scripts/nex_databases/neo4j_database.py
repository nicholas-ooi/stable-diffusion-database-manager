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
import os
import json
import logging
from neo4j import GraphDatabase
import ipfshttpclient
import tempfile
from modules import generation_parameters_copypaste
from modules import shared
from .setting_button import OptionButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jDatabase:

    name = "Neo4j"
    driver = None
    session_instance = None
    components = None

    def __init__(self):
        shared.options_templates.update(
            shared.options_section(
                ('nex-databases', "Nex databases"), {
                    f'nex_databases_enable_neo4j': shared.OptionInfo(False, 'Enable - Neo4j'),
                    f'nex_databases_connection_string_neo4j': shared.OptionInfo(
                        "", 'connection String - Neo4j', gr.Textbox,
                        {'placeholder': 'bolt://localhost:7687'}
                    ),
                    f'nex_databases_user_name_neo4j': shared.OptionInfo("", 'Username - Neo4j'),
                    f'nex_databases_password_neo4j': shared.OptionInfo("", 'Password - Neo4j'),
                    f'nex_databases_test_button_neo4j': OptionButton('Test - Neo4j!', self.test_connectivity),
                }
            )
        )

    def instance(self):
        self.driver = GraphDatabase.driver(
            shared.opts.nex_databases_connection_string_neo4j,
            auth=(shared.opts.nex_databases_user_name_neo4j, shared.opts.nex_databases_password_neo4j)
        )
        self.session_instance = self.driver.session()

    def test_connectivity(self):
        try:
            self.instance()
            self.session_instance.run("RETURN 1 AS connectivity_test")
            message = f"Connected successfully to {self.name}!"
            gr.Info(message)
        except Exception as e:
            message = f"Error connecting to {self.name}: {str(e)}"
            gr.Warning(message)
        finally:
            self.close()

    def insert(self, processed):
        if not shared.opts.nex_databases_enable_neo4j:
            return

        self.instance()

        try:
            with ipfshttpclient.connect() as client:
                for i in range(len(processed.images)):

                    metadata = json.dumps(generation_parameters_copypaste.parse_generation_parameters(processed.infotexts[i]))

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
