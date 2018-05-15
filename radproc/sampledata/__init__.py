# -*- coding: utf-8 -*-

def get_projection_file_path():
    from os.path import dirname, abspath, join
    #sampledataPath = os.path.split(__file__)[0]
    sampledataPath = dirname(abspath(__file__))
    projectionFile = "radolan_proj.prj"
    projectionFilePath = join(sampledataPath, projectionFile)

    return projectionFilePath



