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
from io import BytesIO
import re
import json
from sqlalchemy import create_engine, Column, String, LargeBinary, Integer, text, inspect, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class MySQLDatabase:

    name = "MySQL"
    connection = None
    session_instance = None
    components = None

    header = gr.Label(label=name, value=name, visible=False)
    connection_string = gr.Textbox(label="Connection String", visible=False, placeholder="mysql+mysqlconnector://root:your_password@localhost:3306/your_database_name")
    table_name = gr.Textbox(label="Table Name", visible=False, placeholder="Provide the name of the table")
    image_metadata_column = gr.Textbox(label="Image Metadata Column Name", visible=False, placeholder="Provide the name of the column that stores the image metadata details")
    image_bytes_column = gr.Textbox(label="Image Bytes Column Name", visible=False, placeholder="Provide the name of the column that stores the image")
    connection_result_textarea = gr.TextArea(interactive=False, label='Connection Result', visible=False)
    test_button = gr.Button(value="Test Connection", visible=False)

    def __init__(self):
        self.bind_event_handlers()
        self.components = [
            self.header,
            self.connection_string,
            self.table_name,
            self.image_metadata_column,
            self.image_bytes_column,
            self.connection_result_textarea,
            self.test_button
        ]

    def bind_event_handlers(self):
        self.test_button.click(fn=self.test_connectivity, inputs=[self.connection_string], outputs=[self.connection_result_textarea])

    def instance(self, connection_string):
        self.connection = create_engine(connection_string)
        Session = sessionmaker(bind=self.connection)
        self.session_instance = Session()

    def test_connectivity(self, connection_string):
        message = ""
        try:
            self.instance(connection_string)
            with self.connection.connect() as conn:
                conn.execute(text("SELECT 1"))
            message = f"Connected successfully to {self.name}!\n"
        except Exception as e:
            message = f"Error connecting to {self.name}: {str(e)}"
        finally:
            self.close()
            return message

    def insert(self, processed, input_values):

        # These input values are obtained in order from self.components.
        # This was how stable-diffusion was designed when returning values from various inputs.
        connection_string, table_name, image_metadata_column, image_bytes_column = input_values[1:4]

        self.instance(connection_string)

        try:
            table = self.get_or_create_table(table_name, image_metadata_column, image_bytes_column)
        except Exception as e:
            logger.error(f"Error obtaining the table: {e}")
            raise e
        
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
            buffer = BytesIO()
            image.save(buffer, "png")
            image_bytes = buffer.getvalue()

            data = {
                image_metadata_column: metadata,
                image_bytes_column: image_bytes
            }

            try:
                self.insert_data(table, **data)
                self.session_instance.commit()
            except Exception as e:
                self.session_instance.rollback()
                logger.error(f"Error inserting data: {e}")
                raise e
            finally:
                 self.session_instance.close()


    def close(self):
        if self.connection:
            self.connection.dispose()
            self.connection = None

    def insert_data(self, table, **data):
        if isinstance(table, Table):
            stmt = table.insert().values(**data)
            self.session_instance.execute(stmt)
        else:
            new_row = table(**data)
            self.session_instance.add(new_row)
        self.session_instance.commit()

    def get_or_create_table(self, tbl_name, column1_name, column2_name):
        insp = inspect(self.connection)
        if tbl_name not in insp.get_table_names():
            return self.create_table_and_orm_class(tbl_name, column1_name, column2_name)
        return self.load_table(tbl_name)

    def create_table_and_orm_class(self, tbl_name, column1_name, column2_name):
        class_table = type(
            tbl_name,
            (Base,),
            {
                '__tablename__': tbl_name,
                'id': Column(Integer, primary_key=True, index=True, autoincrement=True),
                column1_name: Column(String(255)),
                column2_name: Column(LargeBinary(length=4294967295))
            }
        )

        Base.metadata.create_all(bind=self.connection)
        return class_table

    def load_table(self, tbl_name):
        return Table(tbl_name, Base.metadata, autoload_with=self.connection)
