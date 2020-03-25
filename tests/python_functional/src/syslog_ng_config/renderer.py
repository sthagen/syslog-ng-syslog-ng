#!/usr/bin/env python
#############################################################################
# Copyright (c) 2015-2018 Balabit
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# As an additional exemption you are allowed to compile & link against the
# OpenSSL libraries as published by the OpenSSL project. See the file
# COPYING for details.
#
#############################################################################


def render_version(version):
    return "@version: {}\n".format(version)


def render_includes(includes):
    include_lines = ['@include "{}"'.format(include) for include in includes]
    return "\n".join(include_lines)


def render_global_options(global_options):
    globals_options_header = "options {\n"
    globals_options_footer = "};\n"

    config_snippet = globals_options_header
    for option_name, option_value in global_options.items():
        config_snippet += "    {}({});\n".format(option_name, option_value)
    config_snippet += globals_options_footer

    return config_snippet


def render_positional_options(positional_parameters):
    config_snippet = ""
    for parameter in positional_parameters:
        config_snippet += "        {}\n".format(str(parameter))
    return config_snippet


def render_driver_options(driver_options):
    config_snippet = ""

    for option_name, option_value in driver_options.items():
        if isinstance(option_value, dict):
            config_snippet += "        {}(\n".format(option_name)
            config_snippet += render_driver_options(option_value)
            config_snippet += "        )\n"
        elif (isinstance(option_value, tuple) or isinstance(option_value, list)):
            for element in option_value:
                config_snippet += "        {}({})\n".format(option_name, element)
        else:
            config_snippet += "        {}({})\n".format(option_name, option_value)

    return config_snippet


def render_statement_groups(statement_groups):
    config_snippet = ""

    for statement_group in statement_groups:
        # statement header
        config_snippet += "\n{} {} {{\n".format(
            statement_group.group_type, statement_group.group_id,
        )

        for statement in statement_group:
            # driver header
            config_snippet += "    {} (\n".format(statement.driver_name)

            # driver options
            config_snippet += render_positional_options(statement.positional_parameters)
            config_snippet += render_driver_options(statement.options)

            # driver footer
            config_snippet += "    );\n"

            # statement footer
        config_snippet += "};\n"

    return config_snippet


def render_logpath_groups(logpath_groups):
    config_snippet = ""

    for logpath_group in logpath_groups:
        config_snippet += "\nlog {\n"
        for statement_group in logpath_group.logpath:
            if statement_group.group_type == "log":
                config_snippet += render_logpath_groups(logpath_groups=[statement_group])
            else:
                config_snippet += "    {}({});\n".format(
                    statement_group.group_type, statement_group.group_id,
                )
        if logpath_group.flags:
            config_snippet += "    flags({});\n".format("".join(logpath_group.flags))
        config_snippet += "};\n"

    return config_snippet


class ConfigRenderer(object):
    def __init__(self, syslog_ng_config):
        self.__syslog_ng_config = syslog_ng_config
        self.__syslog_ng_config_content = ""
        self.__render()

    def get_rendered_config(self):
        return self.__syslog_ng_config_content

    def __render(self, re_create_config=None):

        version = self.__syslog_ng_config["version"]
        includes = self.__syslog_ng_config["includes"]
        global_options = self.__syslog_ng_config["global_options"]
        statement_groups = self.__syslog_ng_config["statement_groups"]
        logpath_groups = self.__syslog_ng_config["logpath_groups"]

        config = ""

        if version:
            config += render_version(version)
        if includes:
            config += render_includes(includes)
        if global_options:
            config += render_global_options(global_options)
        if statement_groups:
            config += render_statement_groups(statement_groups)
        if logpath_groups:
            config += render_logpath_groups(logpath_groups)

        if re_create_config:
            self.__syslog_ng_config_content = config
        else:
            self.__syslog_ng_config_content += config
