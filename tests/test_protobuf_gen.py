import os
import sys
import time
import unittest
from enum import Enum
from importlib import import_module, invalidate_caches, reload
from tempfile import mkdtemp

import pkg_resources
from google.protobuf import descriptor_pool

from protobuf_gen.abstract import Service, Message
from protobuf_gen.main import transpile
from protobuf_gen.patch import ServiceMethodPatch
from protobuf_gen.transpiler import InputModule


class TestProtobufGenerator(unittest.TestCase):
    def test_all(self):
        dir_test = os.path.dirname(__file__)

        my_dir = mkdtemp()

        mod_root = 'protobuf_gen_test'
        wrapper_root = 'wrappers'
        autogen_root = '_autogen'

        with self.subTest('build'):
            patch = [
                ServiceMethodPatch('Radio', 'AnotherRandomNumber', True, True),
            ]

            transpile(
                output_dir_wrappers=os.path.join(my_dir, mod_root, wrapper_root),
                output_dir_autogen=os.path.join(my_dir, mod_root, autogen_root),
                root_module=mod_root,
                root_autogen=mod_root + '.' + autogen_root,
                includes=[
                    os.path.join(dir_test, 'pb_include/mock'),
                    os.path.join(dir_test, 'pb_include/grpc-gateway/third_party/googleapis'),
                    pkg_resources.resource_filename('grpc_tools', '_proto'),
                ],
                input_proto=[
                    os.path.join('protobuf_gen_test/server.proto'),
                    os.path.join('protobuf_gen_test/another.proto'),
                    os.path.join('google/api/annotations.proto'),
                    os.path.join('google/api/http.proto'),
                ],
                output_files={
                    'server.py': InputModule('wrappers.server', 'protobuf_gen_test/server.proto', patch),
                    'another.py': InputModule('wrappers.another', 'protobuf_gen_test/another.proto'),
                }
            )

        with self.subTest('import_final_mod'):
            sys.path += [my_dir]

            srv = import_module(mod_root + '.' + wrapper_root + '.' + 'server')
            ano = import_module(mod_root + '.' + wrapper_root + '.' + 'another')

            srv_names = dir(srv)
            ano_names = dir(ano)

            self.assertTrue(issubclass(srv.Radio, Service))
            self.assertTrue(issubclass(srv.RandomNumberRequest, Message))
            self.assertTrue(issubclass(srv.RandomNumberResponse, Message))
            self.assertTrue(issubclass(srv.RandomNumberRequest.SortOrder, Enum))
            self.assertTrue(issubclass(ano.SortOrder, Enum))
            self.assertTrue(issubclass(ano.AnotherRandomNumberRequest, Message))
            self.assertTrue(issubclass(ano.AnotherRandomNumberResponse, Message))

        with self.subTest('test_serialization_fw'):
            ITEMS_INIT = [
                srv.RandomNumberRequest(),
                srv.RandomNumberResponse(int_responses=[1, 2, 3, 4], obj_responses=[srv.RandomNumber(123)]),
                srv.EnumList([srv.EnumList.ABC.A, srv.EnumList.ABC.B]),
            ]

            ITEMS_PB = [
                x.to_pb() for x in ITEMS_INIT
            ]

            ITEMS_CLS = [
                x.__class__ for x in ITEMS_INIT
            ]

        with self.subTest('test_serialization_backward'):
            ITEMS_AFTER_PB = [
                cls.from_pb(x) for cls, x in zip(ITEMS_CLS, ITEMS_PB)
            ]

            for x, y in zip(ITEMS_INIT, ITEMS_AFTER_PB):
                self.assertEqual(x, y)
