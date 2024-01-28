from WOOD_DESIGN.mainshearwall import MainShearwall
from WOOD_DESIGN.reports import Sqlreports
from UI_Wood.stableVersion5.Sync.data import Data
from UI_Wood.stableVersion5.Sync.Image import saveImage
from UI_Wood.stableVersion5.Sync.postSync import PostSync
from UI_Wood.stableVersion5.Sync.postSync2 import PostSync2
from UI_Wood.stableVersion5.Sync.joistSync import joistAnalysisSync
from UI_Wood.stableVersion5.Sync.beamSync import beamAnalysisSync, BeamSync
from UI_Wood.stableVersion5.Sync.shearWallSync import ShearWallSync, ControlSeismicParameter, ControlMidLine, \
    NoShearWallLines, MidlineEdit, ShearWallStoryCount
from UI_Wood.stableVersion5.Sync.studWallSync import StudWallSync
from UI_Wood.stableVersion5.post_new import magnification_factor
from UI_Wood.stableVersion5.report.ReportGenerator import ReportGeneratorTab
from UI_Wood.stableVersion5.layout.tab_widget2 import secondTabWidgetLayout
from UI_Wood.stableVersion5.output.joist_output import Joist_output
from UI_Wood.stableVersion5.Sync.shearWallSync2 import ShearWallSync2
from UI_Wood.stableVersion5.Sync.studWallSync2 import StudWallSync2
from UI_Wood.stableVersion5.run.beam import BeamStoryBy
from UI_Wood.stableVersion5.run.post import PostStoryBy
from UI_Wood.stableVersion5.run.joist import JoistStoryBy

from PySide6.QtWidgets import QDialog
import time


class mainSync2(Data):
    def __init__(self, saveFunc, grid, tabWidgetCount, GridDrawClass, unlockButton):
        super().__init__()
        self.saveFunc = saveFunc
        self.grid = grid
        self.tabWidgetCount = tabWidgetCount
        self.unlockButton = unlockButton
        self.reportGenerator = None
        self.ReportTab = None
        self.postRun = False
        self.beamRun = False
        self.joistRun = False
        self.shearWallRun = False
        self.studWallRun = False
        self.BeamDesigned = []
        self.PostDesigned = []
        self.JoistDesigned = []
        self.GridDrawClass = GridDrawClass
        self.posts = []
        self.beams = []
        self.joists = []
        self.shearWalls = []
        self.studWalls = []
        self.db = Sqlreports()

    def send_report_generator(self, reportGenerator):
        self.reportGenerator = reportGenerator

    def Run_and_Analysis_Post(self):
        midLineDict = {}
        for currentTab in range(self.tabWidgetCount - 1, -1, -1):
            midLineData, lineLabels, boundaryLineLabels = self.grid[currentTab].run_control()
            if currentTab == self.tabWidgetCount - 1:
                storyName = "Roof"
            else:
                storyName = str(currentTab + 1)

            midLineDict[storyName] = midLineData
            saveImage(self.grid, currentTab)

        self.saveFunc()

        generalProp = ControlGeneralProp(self.general_properties)
        if not self.postRun:
            tabReversed = self.reverse_dict(self.tab)  # top to bottom
            height_from_top = list(reversed(generalProp.height))

            self.db.beam_table()
            self.db.post_table()
            postSync = PostSync(self.db)
            self.posts = []
            if not self.beamRun:
                self.beams = []
                self.shearWalls = []
                beamSync = BeamSync(self.db, self.tabWidgetCount - 1)

            postTop = None
            j = 0
            for i, Tab in tabReversed.items():
                post = Tab["post"]
                if not self.beamRun:
                    beam = Tab["beam"]
                    shearWall = Tab["shearWall"]
                    beamSync.AnalyseDesign(beam, post, shearWall, i)
                    self.beams.append(beam)
                    self.shearWalls.append(shearWall)

                postSync.AnalyseDesign(post, height_from_top[j], i, postTop)
                postStoryDesigned = PostStoryBy(postSync.PostStories[j], self.GridDrawClass, i + 1)
                postTop = post
                self.posts.append(post)
                j += 1
                if i == 0:
                    self.beamRun = True
                    self.postRun = True
                if postStoryDesigned.result == QDialog.Accepted:
                    continue
                else:
                    break
            self.PostDesigned = postSync.PostStories
            if not self.BeamDesigned:
                self.BeamDesigned = beamSync.BeamStories

        else:
            for i, item in enumerate(self.PostDesigned):
                postStoryDesigned = PostStoryBy(item, self.GridDrawClass, len(self.PostDesigned) - i)
                if postStoryDesigned.result == QDialog.Accepted:
                    continue
                else:
                    break

        if self.postRun and self.beamRun and self.joistRun and self.shearWallRun and self.studWallRun:
            self.reportGenerator.setEnabled(True)

        for grid in self.grid:
            grid.setEnabled(False)

        self.unlockButton.setEnabled(True)

    def Run_and_Analysis_Beam(self):

        midLineDict = {}
        for currentTab in range(self.tabWidgetCount - 1, -1, -1):
            midLineData, lineLabels, boundaryLineLabels = self.grid[currentTab].run_control()
            if currentTab == self.tabWidgetCount - 1:
                storyName = "Roof"
            else:
                storyName = str(currentTab + 1)
            midLineDict[storyName] = midLineData
            saveImage(self.grid, currentTab)

        self.saveFunc()

        if not self.beamRun and not self.postRun:
            self.db.beam_table()
            self.db.post_table()
            beamSync = BeamSync(self.db, self.tabWidgetCount - 1)
            self.posts = []
            self.beams = []
            self.shearWalls = []
            tabReversed = self.reverse_dict(self.tab)  # top to bottom
            j = 0
            for i, Tab in tabReversed.items():
                post = Tab["post"]
                beam = Tab["beam"]
                shearWall = Tab["shearWall"]

                c = time.time()
                beamSync.AnalyseDesign(beam, post, shearWall, i)
                d = time.time()
                print(f"Beam analysis story {i} takes ", (d - c) / 60, "Minutes")

                self.posts.append(post)
                self.beams.append(beam)
                self.shearWalls.append(shearWall)

                storyByStoryInstance = BeamStoryBy(beamSync.BeamStories[j], self.GridDrawClass, i + 1)
                j += 1
                if i == 0:
                    self.beamRun = True
                if storyByStoryInstance.result == QDialog.Accepted:
                    continue
                else:
                    break
            self.BeamDesigned = beamSync.BeamStories

        else:
            for i, item in enumerate(self.BeamDesigned):
                storyByStoryInstance = BeamStoryBy(item, self.GridDrawClass, len(self.BeamDesigned) - i)
                if storyByStoryInstance.result == QDialog.Accepted:
                    continue
                else:
                    break

        if self.postRun and self.beamRun and self.joistRun and self.shearWallRun and self.studWallRun:
            self.reportGenerator.setEnabled(True)

        for grid in self.grid:
            grid.setEnabled(False)
        self.unlockButton.setEnabled(True)

    def Run_and_Analysis_Joist(self):
        midLineDict = {}
        for currentTab in range(self.tabWidgetCount - 1, -1, -1):
            midLineData, lineLabels, boundaryLineLabels = self.grid[currentTab].run_control()
            if currentTab == self.tabWidgetCount - 1:
                storyName = "Roof"
            else:
                storyName = str(currentTab + 1)

            midLineDict[storyName] = midLineData
            saveImage(self.grid, currentTab)

        self.saveFunc()

        generalProp = ControlGeneralProp(self.general_properties)
        # TabData = ControlTab(self.tab, generalProp, self.general_information)
        if not self.joistRun:
            self.db.joist_table()
            self.joists = []
            tabReversed = self.reverse_dict(self.tab)  # top to bottom
            joistSync = joistAnalysisSync(self.db)
            j = 0
            for i, Tab in tabReversed.items():
                joist = Tab["joist"]
                joistSync.AnalyseDesign(joist, i)

                self.joists.append(joist)

                storyByStoryInstance = JoistStoryBy(joistSync.JoistStories[j], self.GridDrawClass, i + 1)
                j += 1
                if i == 0:
                    self.joistRun = True
                if storyByStoryInstance.result == QDialog.Accepted:
                    continue
                else:
                    break
            self.JoistDesigned = joistSync.JoistStories
        else:
            for i, item in enumerate(self.JoistDesigned):
                storyByStoryInstance = JoistStoryBy(item, self.GridDrawClass, len(self.JoistDesigned) - i)
                if storyByStoryInstance.result == QDialog.Accepted:
                    continue
                else:
                    break

        # Design should be started from Roof.
        # self.joists.reverse()

        # CREATE DB FOR OUTPUT.

        # # JOIST
        # a = time.time()
        # joistAnalysisInstance = joistAnalysisSync(self.joists, self.db, self.GridDrawClass, True, self.joistRun)
        # self.JoistDesigned = joistAnalysisInstance.JoistStories
        # b = time.time()
        # self.joistRun = joistAnalysisInstance.report
        #
        # print("Joist analysis takes ", (b - a) / 60, "Minutes")
        if self.postRun and self.beamRun and self.joistRun and self.shearWallRun and self.studWallRun:
            self.reportGenerator.setEnabled(True)
        for grid in self.grid:
            grid.setEnabled(False)
        self.unlockButton.setEnabled(True)

    def Run_and_Analysis_ShearWall(self):

        # self.reportGenerator.setEnabled(True)
        midLineDict = {}
        lineLabels = None
        boundaryLineLabels = None
        for currentTab in range(self.tabWidgetCount - 1, -1, -1):
            midLineData, lineLabels, boundaryLineLabels = self.grid[currentTab].run_control()
            if currentTab == self.tabWidgetCount - 1:
                storyName = "Roof"
                ShearWallStoryCount.storyFinal = str(currentTab + 1)

            else:
                storyName = str(currentTab + 1)

            midLineDict[storyName] = midLineData
            saveImage(self.grid, currentTab)

        self.saveFunc()
        if self.shearWallRun:
            dataInstance = ShearWallSync2(self.GridDrawClass)
        else:
            self.shearWalls = []
            self.joists = []

            for i, Tab in self.tab.items():
                shearWall = Tab["shearWall"]
                joist = Tab["joist"]

                self.joists.append(joist)

                self.shearWalls.append(shearWall)

            # Design should be started from Roof.
            # self.shearWalls.reverse()

            generalProp = ControlGeneralProp(self.general_properties)
            joistOutput = Joist_output(self.joists)

            # SHEAR WALL
            # self.loadMapArea, self.loadMapMag = LoadMapArea(self.loadMaps)
            JoistArea = JoistSumArea(self.joists)
            storyName = StoryName(self.joists)  # item that I sent is not important, every element is ok.
            shearWallSync = ShearWallSync(self.shearWalls, generalProp.height, self.db)
            self.studWallSync = StudWallSync(self.studWalls, generalProp.height)

            shearWallExistLine = shearWallSync.shearWallOutPut.shearWallExistLine
            noShearWallLines = NoShearWallLines(shearWallExistLine, set(lineLabels))
            midLineInstance = MidlineEdit(lineLabels, midLineDict, noShearWallLines)
            midLineDictEdited = midLineInstance.newMidline
            # boundaryLineNoShearWall = midLineInstance.boundaryLineNoShearWall
            LoadMapaArea, LoadMapMag = LoadMapAreaNew(midLineDictEdited)
            seismicInstance = ControlSeismicParameter(self.seismic_parameters, storyName, LoadMapaArea, LoadMapMag,
                                                      JoistArea)
            ControlMidLine(midLineDictEdited)

            print(seismicInstance.seismicPara)
            print(midLineDictEdited)
            a = time.time()
            MainShearwall(seismicInstance.seismicPara, midLineDictEdited)
            b = time.time()
            print("Shear wall run takes ", (b - a) / 60, " Minutes")
            self.shearWallRun = True
            dataInstance = ShearWallSync2(self.GridDrawClass)

        print(
            f"beam {self.beamRun}, post {self.postRun}, joist {self.joistRun}, shear wall {self.shearWallRun}, stud wall {self.studWallRun}")
        if self.postRun and self.beamRun and self.joistRun and self.shearWallRun and self.studWallRun:
            self.reportGenerator.setEnabled(True)
        for grid in self.grid:
            grid.setEnabled(False)
        self.unlockButton.setEnabled(True)

    def Run_and_Analysis_StudWall(self):
        self.reportGenerator.setEnabled(True)
        midLineDict = {}
        lineLabels = None
        boundaryLineLabels = None
        for currentTab in range(self.tabWidgetCount - 1, -1, -1):
            midLineData, lineLabels, boundaryLineLabels = self.grid[currentTab].run_control()
            if currentTab == self.tabWidgetCount - 1:
                storyName = "Roof"
                ShearWallStoryCount.storyFinal = str(currentTab + 1)

            else:
                storyName = str(currentTab + 1)
            midLineDict[storyName] = midLineData
            saveImage(self.grid, currentTab)

        self.saveFunc()

        self.studWalls = []

        for i, Tab in self.tab.items():
            studWall = Tab["studWall"]

            self.studWalls.append(studWall)
        generalProp = ControlGeneralProp(self.general_properties)
        studWallSync = StudWallSync(self.studWalls, generalProp.height)
        dataInstance = StudWallSync2(self.GridDrawClass)

        self.studWallRun = True
        if self.postRun and self.beamRun and self.joistRun and self.shearWallRun and self.studWallRun:
            self.reportGenerator.setEnabled(True)
        for grid in self.grid:
            grid.setEnabled(False)
        self.unlockButton.setEnabled(True)

    @staticmethod
    def reverse_dict(Dict):
        key = list(Dict.keys())
        value = list(Dict.values())
        key.reverse()
        value.reverse()
        newDict = {}
        for k, v in zip(key, value):
            newDict[k] = v

        return newDict

    def Unlock(self):
        self.unlockButton.setEnabled(False)
        for grid in self.grid:
            grid.setEnabled(True)
        self.postRun = False
        self.beamRun = False
        self.joistRun = False
        self.shearWallRun = False
        self.studWallRun = False
        self.BeamDesigned.clear()
        self.PostDesigned.clear()
        self.JoistDesigned.clear()
        self.reportGenerator.setEnabled(False)


class ControlGeneralProp:
    def __init__(self, generalProp):
        self.generalProp = generalProp
        self.height = [i / magnification_factor for i in self.control_inputs(generalProp["height_story"])]
        self.Hn = sum(self.height) / magnification_factor

    @staticmethod
    def control_inputs(item):
        if item:
            # better appearance
            item = [i * magnification_factor for i in item]
        else:
            item = [10 * magnification_factor]  # 10 ft or 10 m

        return item


def LoadMapArea(loadMaps):
    areaListFull = []
    magListFull = []
    for i, loadMapTab in enumerate(loadMaps):
        areaList = []
        magList = []
        for loadMap in loadMapTab:
            for load in loadMap["load"]:
                if load["type"] == "Dead Super":
                    areaList.append(loadMap["area"] / (magnification_factor ** 2))
                    magList.append(load["magnitude"])
        areaListFull.append(areaList)
        magListFull.append(magList)

    return areaListFull, magListFull


def LoadMapAreaNew(midLine):
    areaListFull = []
    magListFull = []
    controlLines = [str(i) for i in range(1000)]  # 1000 is just a big number
    for i, loadMapTab in midLine.items():
        magList = []
        areaList = []
        for LoadProp in loadMapTab:
            line = list(LoadProp.keys())[0]
            if line in controlLines:
                for loadMap in LoadProp.values():
                    for load in loadMap:
                        areaList.append(load["area"])
                        magList.append(load["magnitude"])
        areaListFull.append(areaList)
        magListFull.append(magList)

    return areaListFull, magListFull


def JoistSumArea(joists):
    JoistArea = []
    for joistTab in joists:
        area = 0
        for joist in joistTab:
            area += joist["area"] / (magnification_factor ** 2)
        JoistArea.append(area)

    return JoistArea


def StoryName(item):
    storyList = []
    storyNumber = len(item)
    for i in range(storyNumber):
        if i < storyNumber - 1:
            storyList.append(f"{i + 1}")
        else:
            storyList.append("Roof")
    storyList.reverse()
    return storyList
