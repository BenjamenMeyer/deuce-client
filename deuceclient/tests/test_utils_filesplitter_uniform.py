"""
Tests - Deuce Client - Utils - File Splitter - Uniform File Splitter
"""
import os
from unittest import TestCase

import mock

import deuceclient.api as api
from deuceclient.utils import UniformSplitter
from deuceclient.tests import *


class TestUniformSplitter(TestCase):

    def setUp(self):
        super(TestUniformSplitter, self).setUp()

        self.project_id = create_project_name()
        self.vault_id = create_vault_name()

    def tearDown(self):
        super(TestUniformSplitter, self).tearDown()

    def test_init(self):
        reader = make_reader(100)

        splitter = UniformSplitter(self.project_id,
                                   self.vault_id,
                                   reader)
        self.assertEqual(self.project_id, splitter.project_id)
        self.assertEqual(self.vault_id, splitter.vault_id)
        self.assertEqual(reader, splitter.input_stream)
        self.assertIsNone(splitter.state)
        self.assertEqual(1024 * 1024, splitter.chunk_size)

    def test_configure(self):
        reader = make_reader(100)

        splitter = UniformSplitter(self.project_id,
                                   self.vault_id,
                                   reader)
        self.assertEqual(1024 * 1024, splitter.chunk_size)

        config = {
            'UniformSplitter': {
                'chunk_size': 5
            }
        }
        splitter.configure(config)
        self.assertEqual(config['UniformSplitter']['chunk_size'],
                         splitter.chunk_size)

    def test_configure_failed(self):
        reader = make_reader(100)

        splitter = UniformSplitter(self.project_id,
                                   self.vault_id,
                                   reader)
        self.assertEqual(1024 * 1024, splitter.chunk_size)

        config = {
            'NonUniformSplitter': {
                'non_chunk_size': 1024
            }
        }
        splitter.configure(config)
        self.assertEqual(1024 * 1024, splitter.chunk_size)

    def test_set_invalid_state(self):
        reader = make_reader(1)

        splitter = UniformSplitter(self.project_id,
                                   self.vault_id,
                                   reader)

        with self.assertRaises(ValueError):
            splitter._set_state('bad state')

    def test_set_reader(self):
        reader = make_reader(1)

        splitter = UniformSplitter(self.project_id,
                                   self.vault_id,
                                   reader)

        self.assertEqual(reader, splitter.input_stream)

        new_reader = make_reader(2)
        splitter.input_stream = new_reader

        self.assertEqual(new_reader, splitter.input_stream)

        splitter._set_state('processing')

        with self.assertRaises(RuntimeError):
            splitter.input_stream = reader

        splitter._set_state(None)

        class X(object):
            pass

        with self.assertRaises(TypeError):
            splitter.input_stream = X()

    def test_get_block(self):
        reader = make_reader(10 * 1024 * 1024)

        splitter = UniformSplitter(self.project_id,
                                   self.vault_id,
                                   reader)

        for _ in range(2):
            block = splitter.get_block()
            self.assertIsInstance(block, api.Block)
            self.assertEqual(splitter.chunk_size, len(block))

    def test_get_block_fail(self):
        reader = make_reader(0)

        splitter = UniformSplitter(self.project_id,
                                   self.vault_id,
                                   reader)

        block = splitter.get_block()
        self.assertIsNone(block)

    def test_make_block(self):
        reader = make_reader(10 * 1024 * 1024)

        splitter = UniformSplitter(self.project_id,
                                   self.vault_id,
                                   reader)
        d = os.urandom(100)
        block = splitter._make_block(d)
        self.assertIsInstance(block, api.Block)
        self.assertEqual(len(d), len(block))

    def test_get_blocks_sufficient_data(self):

        counts = [
            0, 1, 2, 5, 10
        ]

        for count in counts:
            reader = make_reader(11 * 1024 * 1024, use_temp_file=True)

            splitter = UniformSplitter(self.project_id,
                                       self.vault_id,
                                       reader)
            self.assertEqual(splitter.chunk_size,
                             (1024 * 1024))

            blocks = splitter.get_blocks(count)
            self.assertIsInstance(blocks, api.Blocks)
            self.assertEqual(count, len(blocks))
            for block_id, block in blocks.items():
                self.assertIsInstance(block, api.Block)
                self.assertEqual(splitter.chunk_size,
                                 len(block))

    def test_get_blocks_insufficient_data(self):

        counts = [
            2, 5, 10
        ]

        for count in counts:
            reader = make_reader((count - 1) * 1024 * 1024)

            splitter = UniformSplitter(self.project_id,
                                       self.vault_id,
                                       reader)
            self.assertEqual(splitter.chunk_size,
                             (1024 * 1024))

            blocks = splitter.get_blocks(count)
            self.assertIsInstance(blocks, api.Blocks)
            self.assertEqual((count - 1), len(blocks))
            for block_id, block in blocks.items():
                self.assertIsInstance(block, api.Block)
                self.assertEqual(splitter.chunk_size,
                                 len(block))

    def test_get_blocks_insufficient_data_partial_block(self):

        counts = [
            2, 5, 10
        ]

        bytes_remainder = 1024

        for count in counts:
            reader = make_reader(((count - 1) * 1024 * 1024) + bytes_remainder)

            splitter = UniformSplitter(self.project_id,
                                       self.vault_id,
                                       reader)
            self.assertEqual(splitter.chunk_size,
                             (1024 * 1024))

            blocks = splitter.get_blocks(count)
            self.assertIsInstance(blocks, api.Blocks)
            self.assertEqual(count, len(blocks))
            for block_id, block in blocks.items():
                self.assertIsInstance(block, api.Block)
                # one block will be bytes_remainder bytes, the rest
                # will be chunk_size bytes
                if len(block) == bytes_remainder:
                    pass
                else:
                    self.assertEqual(splitter.chunk_size,
                                     len(block))