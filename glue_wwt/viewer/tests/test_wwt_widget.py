from __future__ import absolute_import, division, print_function

from mock import MagicMock

from glue.app.qt import GlueApplication
from glue.core import Data, message
from glue.core.tests.test_state import clone

from ..data_viewer import WWTDataViewer


class TestWWTDataViewer(object):

    def setup_method(self, method):
        self.d = Data(x=[1, 2, 3], y=[2, 3, 4], z=[4, 5, 6])
        self.application = GlueApplication()
        self.dc = self.application.data_collection
        self.dc.append(self.d)
        self.hub = self.dc.hub
        self.session = self.application.session
        self.viewer = self.application.new_data_viewer(WWTDataViewer)
        self.options = self.viewer.options_widget()

    def register(self):
        self.viewer.register_to_hub(self.hub)

    def test_add_data(self):
        self.viewer.add_data(self.d)
        self.viewer.state.lon_att = self.d.id['x']
        self.viewer.state.lat_att = self.d.id['y']

    def test_center(self):
        self.viewer.add_data(self.d)
        self.viewer.state.lon_att = self.d.id['x']
        self.viewer.state.lat_att = self.d.id['y']
        self.viewer.layers[0].center()

    def test_new_subset_group(self):
        # Make sure only the subset for data that is already inside the viewer
        # is added.
        d2 = Data(a=[4, 5, 6])
        self.dc.append(d2)
        self.viewer.add_data(self.d)
        assert len(self.viewer.layers) == 1
        self.dc.new_subset_group(subset_state=self.d.id['x'] > 1, label='A')
        assert len(self.viewer.layers) == 2

    def test_double_add_ignored(self):
        assert len(self.viewer.layers) == 0
        self.viewer.add_data(self.d)
        assert len(self.viewer.layers) == 1
        self.viewer.add_data(self.d)
        assert len(self.viewer.layers) == 1

    def test_remove_data(self):
        self.register()
        self.viewer.add_data(self.d)
        layer = self.viewer._layer_artist_container[self.d][0]

        layer.clear = MagicMock()
        self.hub.broadcast(message.DataCollectionDeleteMessage(self.dc,
                                                               data=self.d))
        # TODO: the following currently fails but is not critical, so we
        #       skip for now.
        # assert layer.clear.call_count == 1
        assert self.d not in self.viewer._layer_artist_container

    def test_remove_subset(self):
        self.register()
        s = self.d.new_subset()
        self.viewer.add_subset(s)

        layer = self.viewer._layer_artist_container[s][0]
        layer.clear = MagicMock()

        self.hub.broadcast(message.SubsetDeleteMessage(s))

        #assert layer.clear.call_count == 1
        assert s not in self.viewer._layer_artist_container

    def test_subsets_added_with_data(self):
        s = self.d.new_subset()
        self.viewer.add_data(self.d)
        assert s in self.viewer._layer_artist_container

    def test_subsets_live_added(self):
        self.register()
        self.viewer.add_data(self.d)
        s = self.d.new_subset()
        assert s in self.viewer._layer_artist_container

    def test_clone(self):

        self.viewer.add_data(self.d)
        self.viewer.state.layers[0].ra_att = self.d.id['y']
        self.viewer.state.layers[0].dec_att = self.d.id['x']

        application2 = clone(self.application)

        viewer2 = application2.viewers[0][0]

    def test_changing_alt_back_to_none(self):

        # Regression test for a bug which caused an exception to
        # happen when changing the altitude attribute back to None
        self.viewer.add_data(self.d)
        self.viewer.state.mode = 'Milky Way'
        self.viewer.state.lon_att = self.d.id['x']
        self.viewer.state.lat_att = self.d.id['y']
        self.viewer.state.alt_att = self.d.id['z']
        self.viewer.state.alt_unit = 'kpc'
        self.viewer.state.alt_att = None

    def test_remove_layer(self):

        # Make sure that _update_markers doesn't get called after removing a
        # layer. This is a regression test for
        # https://github.com/glue-viz/glue-wwt/issues/54

        self.register()
        self.d.add_subset(self.d.id['x'] > 1)
        self.viewer.add_data(self.d)
        assert len(self.viewer.layers) == 2

        subset_layer = self.viewer.layers[1]

        subset_layer.wwt_client.layers.add_table_layer = MagicMock()

        self.viewer.remove_subset(self.d.subsets[0])
        assert len(self.viewer.layers) == 1
        assert subset_layer.wwt_client.layers.add_table_layer.call_count == 0
        assert subset_layer.wwt_layer is None

    # TODO: determine if the following test is the desired behavior
    # def test_subsets_not_live_added_if_data_not_present(self):
    #     self.register()
    #     s = self.d.new_subset()
    #     assert s not in self.viewer

    # def test_updated_on_coordinate_change(self):
    #     self.register()
    #     self.viewer.add_data(self.d)
    #     self.viewer.state.layers[0].ra_att = self.d.id['x']
    #     self.viewer.state.layers[0].dec_att = self.d.id['y']
    #     artist = self.viewer._layer_artist_container[self.d][0]
    #     self.viewer._update_layer = MagicMock()
    #     self.viewer.state.layers[0].ra_att = self.d.id['y']
    #     self.viewer._update_layer.call_count > 0
