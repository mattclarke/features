#! /usr/bin/env python

import h5py
import numpy
import importlib
import sys
import os

RECIPIE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/recipes"
sys.path.append(RECIPIE_DIR)


class InsaneEntryWithFeatures:
    def __init__(self, nxsfile, entrypath, featurearray):
        self.nxsfile = nxsfile
        self.entrypath = entrypath
        self.featurearray = featurearray

    def features(self):
        return self.featurearray

    def feature_response(self, featureid):
        featuremodule = importlib.import_module("%016X.recipe" % featureid)
        r = featuremodule.recipe(self.nxsfile, self.entrypath)
        return r.process()

    def feature_title(self, featureid):
        featuremodule = importlib.import_module("%016X.recipe" % featureid)
        r = featuremodule.recipe(self.nxsfile, self.entrypath)
        return r.title


class InsaneFeatureDiscoverer:
    def __init__(self, nxsfile):
        self.file = h5py.File(nxsfile, 'r')

    def entries(self):
        ent = []
        for entry in self.file.keys():
            path = "/%s/features" % entry
            try:
                features = self.file[path]
                if features.dtype == numpy.dtype("uint64"):
                    ent.append(InsaneEntryWithFeatures(self.file, entry, features))
            except:
                print("no features in " + path)
                pass
        return ent


class AllFeatureDiscoverer:
    def __init__(self, nxsfile):
        self.file = h5py.File(nxsfile, 'r')

    def entries(self):
        ent = []
        for entry in self.file.keys():
            try:
                features = []
                for feat in os.listdir(RECIPIE_DIR):
                    try:
                        features.append(int(feat, 16))
                    except:
                        print("Could not parse feature with name %s" % (feat))
                ent.append(InsaneEntryWithFeatures(self.file, entry, features))
            except:
                print("no recipes in " + RECIPIE_DIR)
                pass
        return ent

class SingleFeatureDiscoverer:
    def __init__(self, nxsfile, feature):
        self.file = h5py.File(nxsfile, 'r')
        self.feature = feature

    def entries(self):
        ent = []
        for entry in self.file.keys():
            try:
                ent.append(InsaneEntryWithFeatures(self.file, entry, [self.feature]))
            except:
                print("Issues with parsing feature %i"% self.feature)
                pass
        return ent


if __name__ == '__main__':
    import argparse
    import traceback

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", dest="test", help="Test file against all recipes", action="store_true",
                        default=False)
    parser.add_argument("-f", "--feature", dest="feature", help="Test file against a defined feature",
                      default=None)
    parser.add_argument("-v", "--verbose", dest="verbose", help="Include full stacktraces of failues", action="store_true",
                        default=False)
    parser.add_argument("nexusfile", help="Nexus file to test")

    args = parser.parse_args()

    if args.feature:
        try:
            disco = SingleFeatureDiscoverer(args.nexusfile, int(args.feature, 16))
        except:
            print("The feature '%s' has not parsed correctly, exiting" %(args.feature))
            sys.exit()
    else:
      if args.test:
          disco = AllFeatureDiscoverer(args.nexusfile)
      else:
          disco = InsaneFeatureDiscoverer(args.nexusfile)

    for entry in disco.entries():
        fail_list = []
        error_list = []

        print("Entry \"%s\" appears to contain the following features (they validate correctly): " % entry.entrypath)
        for feat in entry.features():
            try:
                response = entry.feature_response(feat)
                print("\t%s (%d) %s" % (entry.feature_title(feat), feat, response))
            except AssertionError as ae:
                fail_list.append((feat, str(ae)))
            except Exception as e:
                error_list.append((feat, str(traceback.format_exc())))

        if len(fail_list) > 0:
            print("\n\tThe following features failed to validate:")
            for feat, message in fail_list:
                print("\t\t%s (%d) is invalid with the following errors:" % (entry.feature_title(feat), feat))
                print("\t\t\t" + message.replace('\n', '\n\t\t'))

        if len(error_list) > 0:
            print("\n\tThe following features had unexpected errors (Are you running windows?):")
            for feat, message in error_list:
                try:
                    print("\t\t%s (%d) had an unexpected error" % (entry.feature_title(feat), feat))
                    if args.verbose:
                        print("\t\t\t" + message.replace('\n', '\n\t\t\t'))
                except:
                    print("\t\tFeature (%d) could not be found" % (feat))
        print("\n")
