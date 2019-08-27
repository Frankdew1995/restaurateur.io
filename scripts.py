# import pickle
# from app import app
# from pathlib import Path
#
#
# data = []
#
# # with open (str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'), mode="wb") as pickle_in:
# #
# #     pickle.dump(data, pickle_in)
# #
# # pickle_in.close()
#
#
# with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
#           mode="rb") as pickle_out:
#
#     data = pickle.load(pickle_out)

data = [
        {1: {"lastPrinted": "2013.09.20"}},
        {2: {"lastPrinted": "2013.09.21"}}
    ]

print(data)