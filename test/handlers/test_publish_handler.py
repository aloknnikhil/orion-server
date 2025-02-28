from unittest import TestCase

import flask
import unittest.mock as mock

from orion.clients.cache import CacheClient
from orion.handlers.publish_handler import PublishHandler


class TestPublishHandler(TestCase):
    def setUp(self):
        self.mock_app = flask.Flask(__name__)
        self.mock_ctx = mock.MagicMock()
        self.mock_ctx.cache = CacheClient(addr=None, prefix='prefix')

    def test_metadata(self):
        handler = PublishHandler(ctx=self.mock_ctx)

        self.assertEqual(handler.methods, ['POST'])
        self.assertEqual(handler.path, '/api/publish')

    def test_type_filter(self):
        handler = PublishHandler(ctx=self.mock_ctx, data={'_type': 'lwt'})
        resp, status = handler.run()

        self.assertFalse(resp['success'])
        self.assertEqual(resp['message'], 'Not a location publish.')
        self.assertEqual(status, 400)

    def test_location_report_valid_android(self):
        mock_headers = {
            'X-Limit-U': 'user',
            'X-Limit-D': 'device',
        }

        mock_data = {
            '_type': 'location',
            'lat': 1.0,
            'lon': 2.0,
        }

        self.mock_ctx.geocode.reverse_geocode.return_value = {'place_name': 'address'}

        with self.mock_app.test_request_context(headers=mock_headers):
            handler = PublishHandler(ctx=self.mock_ctx, data=mock_data)
            resp, status = handler.run()
            geocode_args, _ = self.mock_ctx.geocode.reverse_geocode.call_args
            (location,), _ = self.mock_ctx.db.session.add.call_args

            self.assertTrue(resp['success'])
            self.assertEqual(status, 201)
            self.assertEqual(geocode_args, (1.0, 2.0))
            self.assertEqual(location.user, 'user')
            self.assertEqual(location.device, 'device')
            self.assertEqual(location.latitude, 1.0)
            self.assertEqual(location.longitude, 2.0)
            self.assertEqual(location.address, 'address')

    def test_location_report_valid_ios(self):
        mock_data = {
            '_type': 'location',
            'lat': 1.0,
            'lon': 2.0,
            'topic': 'owntracks/user/device'
        }

        self.mock_ctx.geocode.reverse_geocode.return_value = {'place_name': 'address'}

        with self.mock_app.test_request_context():
            handler = PublishHandler(ctx=self.mock_ctx, data=mock_data)
            resp, status = handler.run()
            geocode_args, _ = self.mock_ctx.geocode.reverse_geocode.call_args
            (location,), _ = self.mock_ctx.db.session.add.call_args

            self.assertTrue(resp['success'])
            self.assertEqual(status, 201)
            self.assertEqual(geocode_args, (1.0, 2.0))
            self.assertEqual(location.user, 'user')
            self.assertEqual(location.device, 'device')
            self.assertEqual(location.latitude, 1.0)
            self.assertEqual(location.longitude, 2.0)
            self.assertEqual(location.address, 'address')

    def test_location_report_reverse_geocode_failure(self):
        mock_data = {
            '_type': 'location',
            'lat': 1.0,
            'lon': 2.0,
            'topic': 'owntracks/user/device'
        }

        self.mock_ctx.geocode.reverse_geocode.return_value = None

        with self.mock_app.test_request_context():
            handler = PublishHandler(ctx=self.mock_ctx, data=mock_data)
            resp, status = handler.run()
            geocode_args, _ = self.mock_ctx.geocode.reverse_geocode.call_args
            (location,), _ = self.mock_ctx.db.session.add.call_args

            self.assertTrue(resp['success'])
            self.assertEqual(status, 201)
            self.assertEqual(geocode_args, (1.0, 2.0))
            self.assertEqual(location.user, 'user')
            self.assertEqual(location.device, 'device')
            self.assertEqual(location.latitude, 1.0)
            self.assertEqual(location.longitude, 2.0)
            self.assertIsNone(location.address)

    def test_cmd_report_location(self):
        mock_data = {
            '_type': 'cmd',
            'action': 'reportLocation',
            'topic': 'owntracks/user/device'
        }

        with self.mock_app.test_request_context():
            handler = PublishHandler(ctx=self.mock_ctx, data=mock_data)
            resp, status = handler.run()

            self.assertTrue(resp['success'])
            self.assertEqual(status, 200)
