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

import modules.scripts as scripts
import gradio as gr
from scripts import nex_databases


class DatabaseManagerNex(scripts.Script):

    def __init__(self):
        super().__init__()
        self.databases = {}
        self.databases_1 = {}

    def initialise_database_names(self):

        for database in nex_databases.all_database_classes:
            class_instance = database()
            self.databases[class_instance.name] = class_instance

    def selected_checkboxes(self, database_checkboxes_values):
        
        ui_components_to_update = []

        for database in self.databases.values():
            visibility = database.name in database_checkboxes_values
            for _ in database.components:
                ui_components_to_update.append(gr.update(visible=visibility))

        return ui_components_to_update

    def title(self):
        return "Database Manager Nex"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):

        database_names = []
        database_ui_components = []

        self.initialise_database_names()
        for database in self.databases.values():
            database_names += [database.name]
            database_ui_components += database.components

        database_checkboxes = gr.CheckboxGroup(choices=database_names, label='Database Types')
        database_checkboxes.select(
            fn=self.selected_checkboxes,
            inputs=[database_checkboxes],
            outputs=database_ui_components
        )

        database_ui_components.append(database_checkboxes)

        return database_ui_components

    def postprocess(self, p, processed, *args):

        selected_databases_from_checkboxes = args[-1]
        grouped_database_values = {}
        start_index = 0
        
        for database in self.databases.values():

            try:
    
                end_index = start_index + len(database.components)
                grouped_database_values[database.name] = args[start_index:end_index]
                start_index = end_index

                if database.name in selected_databases_from_checkboxes:
                    database.insert(processed, grouped_database_values[database.name])
                    
            except Exception as e:
                print(f"Error after post processing: {str(e)}")

        return True
