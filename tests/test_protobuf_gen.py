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


def make_sure_modules_are_purged_from_cache(mod_root):
    invalidate_caches()

    for k, x in sys.modules.items():
        if k.startswith(mod_root):
            print('del', x)
            del x

    # try:
    #
    #     x = import_module(mod_root)
    #     if x is not None:
    #         print(dir(x))
    #         srv = reload(x)
    #     m = import_module(mod_root)
    #     del m
    #     srv = reload(import_module(mod_root))
    # except AttributeError:
    #     pass


class TestProtobufGenerator(unittest.TestCase):
    def test_all(self):
        dir_test = os.path.dirname(__file__)

        my_dir = mkdtemp()
        # my_dir = os.path.join(os.path.dirname(__file__), '_build')

        mod_root = 'protobuf_gen_test'
        autogen_root = 'xyxasdautogen'

        with self.subTest('build'):
            patch = [
                ServiceMethodPatch('Radio', 'AnotherRandomNumber', True, True),
            ]

            transpile(
                output_dir=os.path.join(my_dir, mod_root),
                root_module=mod_root,
                root_autogen=autogen_root,
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
                    'server': InputModule('protobuf_gen_test/server.proto', patch),
                    'another': InputModule('protobuf_gen_test/another.proto'),
                }
            )



        with self.subTest('import_final_mod'):

            descriptor_pool._DEFAULT = descriptor_pool.DescriptorPool()

            # make_sure_modules_are_purged_from_cache(mod_root)
            # make_sure_modules_are_purged_from_cache(mod_root)
            # make_sure_modules_are_purged_from_cache(mod_root)
            # make_sure_modules_are_purged_from_cache(mod_root)
            #
            sys.path += [my_dir]

            # for x in os.walk(my_dir):
            #     print(x)

            # srv = import_module(mod_root)

            srv = import_module(mod_root + '.' + 'server')
            ano = import_module(mod_root + '.' + 'another')

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
