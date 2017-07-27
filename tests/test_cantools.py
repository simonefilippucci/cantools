import os
import unittest
import cantools
import sys

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class CanToolsTest(unittest.TestCase):

    def test_vehicle(self):
        filename = os.path.join('tests', 'files', 'vehicle.dbc')
        db = cantools.db.load_file(filename)
        self.assertEqual(len(db.nodes), 1)
        self.assertEqual(db.nodes[0].name, 'Vector__XXX')
        self.assertEqual(len(db.messages), 217)
        self.assertEqual(db.messages[216].frame_id, 155872546)
        self.assertEqual(str(db.messages[0]),
                         "message('RT_SB_INS_Vel_Body_Axes', 0x9588322, False, 8, None)")
        self.assertEqual(repr(db.messages[0].signals[0]),
                         "signal('INS_Vel_Sideways_2D', 40, 24, 'little_endian', "
                         "True, 0.0001, 0, -838, 838, 'm/s', False, None, None, "
                         "'Sideways Velocity in the vehicle body axes, 2D (no "
                         "vertical component) .  +ve for motion to the vehicle "
                         "RHS.')")
        self.assertEqual(repr(db.nodes[0]), "node('Vector__XXX', None)")
        i = 0

        for message in db.messages:
            for signal in message.signals:
                if signal.choices is not None:
                    i += 1

        self.assertEqual(i, 15)

        with open(filename, 'r') as fin:
            self.assertEqual(db.as_dbc(), fin.read())

    def test_motohawk(self):
        filename = os.path.join('tests', 'files', 'motohawk.dbc')

        with open(filename, 'r') as fin:
            db = cantools.db.load(fin)

        self.assertEqual(len(db.nodes), 2)
        self.assertEqual(db.nodes[0].name, 'PCM1')
        self.assertEqual(db.nodes[1].name, 'FOO')
        self.assertEqual(len(db.messages), 1)
        self.assertEqual(len(db.messages[0].signals[0].nodes), 2)
        self.assertEqual(db.messages[0].signals[0].nodes[0], 'Vector__XXX')
        self.assertEqual(db.messages[0].signals[0].nodes[1], 'FOO')
        self.assertEqual(db.messages[0].signals[1].nodes[0], 'Vector__XXX')

        with open(filename, 'r') as fin:
            self.assertEqual(db.as_dbc(), fin.read())

    def test_emc32(self):
        db = cantools.db.File()
        filename = os.path.join('tests', 'files', 'emc32.dbc')

        with open(filename, 'r') as fin:
            db.add_dbc(fin)

        self.assertEqual(len(db.nodes), 1)
        self.assertEqual(db.nodes[0].name, 'EMV_Statusmeldungen')
        self.assertEqual(len(db.messages), 1)
        self.assertEqual(len(db.messages[0].signals[0].nodes), 1)

    def test_foobar(self):
        db = cantools.db.File()
        filename = os.path.join('tests', 'files', 'foobar.dbc')
        db.add_dbc_file(filename)

        self.assertEqual(len(db.nodes), 2)
        self.assertEqual(db.version, '2.0')
        self.assertEqual(repr(db),
                         "version('2.0')\n"
                         "\n"
                         "node('FOO', None)\n"
                         "node('BAR', 'fam')\n"
                         "\n"
                         "message('Foo', 0x12331, True, 8, 'Foo.')\n"
                         "  signal('Foo', 7, 12, 'big_endian', True, 0.01, "
                         "250, 229.53, 270.47, 'degK', False, None, {-1: \'Foo\', "
                         "-2: \'Fie\'}, None)\n"
                         "  signal('Bar', 1, 6, 'big_endian', False, 0.1, "
                         "0, 1.0, 5.0, 'm', False, None, None, '')\n")

        message = db.lookup_message(0x12331)
        self.assertEqual(message.name, 'Foo')

    def test_motohawk_encode_decode(self):
        """Encode and decode the signals in a ExampleMessage frame.

        """

        db = cantools.db.File()
        filename = os.path.join('tests', 'files', 'motohawk.dbc')
        db.add_dbc_file(filename)

        example_message_frame_id = 496

        # Encode with non-enumerated values.
        data = {
            'Temperature': 250.55,
            'AverageRadius': 3.2,
            'Enable': 1
        }

        encoded = db.encode_message(example_message_frame_id, data)
        self.assertEqual(encoded, b'\xc1\x1b\x00\x00\x00\x00\x00\x00')

        # Encode with enumerated values.
        data = {
            'Temperature': 250.55,
            'AverageRadius': 3.2,
            'Enable': 'Enabled'
        }

        encoded = db.encode_message(example_message_frame_id, data)
        self.assertEqual(encoded, b'\xc1\x1b\x00\x00\x00\x00\x00\x00')

        decoded = db.decode_message(example_message_frame_id, encoded)
        self.assertEqual(decoded, data)

    def test_socialledge(self):
        db = cantools.db.File()
        filename = os.path.join('tests', 'files', 'socialledge.dbc')
        db.add_dbc_file(filename)

        # Verify nodes.
        self.assertEqual(len(db.nodes), 5)
        self.assertEqual(db.nodes[0].name, 'DBG')
        self.assertEqual(db.nodes[0].comment, None)
        self.assertEqual(db.nodes[1].name, 'DRIVER')
        self.assertEqual(db.nodes[1].comment,
                         'The driver controller driving the car')
        self.assertEqual(db.nodes[2].name, 'IO')
        self.assertEqual(db.nodes[2].comment, None)
        self.assertEqual(db.nodes[3].name, 'MOTOR')
        self.assertEqual(db.nodes[3].comment,
                         'The motor controller of the car')
        self.assertEqual(db.nodes[4].name, 'SENSOR')
        self.assertEqual(db.nodes[4].comment,
                         'The sensor controller of the car')

        # Verify messages and their signals.
        self.assertEqual(len(db.messages), 5)
        self.assertEqual(db.messages[0].name, 'DRIVER_HEARTBEAT')
        self.assertEqual(db.messages[0].comment,
                         'Sync message used to synchronize the controllers')
        self.assertEqual(db.messages[0].signals[0].choices[0],
                         'DRIVER_HEARTBEAT_cmd_NOOP')
        self.assertEqual(db.messages[0].signals[0].choices[1],
                         'DRIVER_HEARTBEAT_cmd_SYNC')
        self.assertEqual(db.messages[0].signals[0].choices[2],
                         'DRIVER_HEARTBEAT_cmd_REBOOT')
        self.assertEqual(db.messages[1].name, 'IO_DEBUG')
        self.assertEqual(db.messages[2].name, 'MOTOR_CMD')
        self.assertEqual(db.messages[3].name, 'MOTOR_STATUS')
        self.assertEqual(db.messages[4].name, 'SENSOR_SONARS')

        sensor_sonars = db.messages[-1]
        
        self.assertFalse(db.messages[0].is_multiplexed())
        self.assertTrue(sensor_sonars.is_multiplexed())
        self.assertEqual(sensor_sonars.signals[0].name, 'SENSOR_SONARS_no_filt_rear')
        self.assertEqual(sensor_sonars.signals[0].multiplexer_id, 1)
        self.assertEqual(sensor_sonars.signals[-3].name, 'SENSOR_SONARS_left')
        self.assertEqual(sensor_sonars.signals[-3].multiplexer_id, 0)
        self.assertEqual(sensor_sonars.signals[-1].name, 'SENSOR_SONARS_mux')
        self.assertEqual(sensor_sonars.signals[-1].is_multiplexer, True)

        self.assertEqual(sensor_sonars.get_multiplexer_signal_name(),
                         'SENSOR_SONARS_mux')
        signals = sensor_sonars.get_signals_by_multiplexer_id(0)
        self.assertEqual(len(signals), 6)
        self.assertEqual(signals[0].name, 'SENSOR_SONARS_rear')

        self.assertEqual(db.version, '')

    def test_socialledge_encode_decode_mux_0(self):
        """Encode and decode the signals in a SENSOR_SONARS frame with mux 0.

        """

        db = cantools.db.File()
        filename = os.path.join('tests', 'files', 'socialledge.dbc')
        db.add_dbc_file(filename)

        frame_id = 200
        data = {
            'SENSOR_SONARS_mux': 0,
            'SENSOR_SONARS_err_count': 1,
            'SENSOR_SONARS_left': 2,
            'SENSOR_SONARS_middle': 3,
            'SENSOR_SONARS_right': 4,
            'SENSOR_SONARS_rear': 5
        }

        encoded = db.encode_message(frame_id, data)
        self.assertEqual(encoded, b'\x10\x00\x14\xe0\x01( \x03')

        decoded = db.decode_message(frame_id, encoded)
        self.assertEqual(decoded, data)

    def test_socialledge_encode_decode_mux_1(self):
        """Encode and decode the signals in a SENSOR_SONARS frame with mux 1.

        """

        db = cantools.db.File()
        filename = os.path.join('tests', 'files', 'socialledge.dbc')
        db.add_dbc_file(filename)

        frame_id = 200
        data = {
            'SENSOR_SONARS_mux': 1,
            'SENSOR_SONARS_err_count': 2,
            'SENSOR_SONARS_no_filt_left': 3,
            'SENSOR_SONARS_no_filt_middle': 4,
            'SENSOR_SONARS_no_filt_right': 5,
            'SENSOR_SONARS_no_filt_rear': 6
        }

        encoded = db.encode_message(frame_id, data)
        self.assertEqual(encoded, b'!\x00\x1e\x80\x022\xc0\x03')

        decoded = db.decode_message(frame_id, encoded)
        self.assertEqual(decoded, data)

    def test_add_message(self):
        db = cantools.db.File()
        signals = [cantools.db.Signal(name='signal',
                                      start=0,
                                      length=4,
                                      nodes=['foo'],
                                      byte_order='big_endian',
                                      is_signed=False,
                                      scale=1.0,
                                      offset=10,
                                      minimum=10.0,
                                      maximum=100.0,
                                      unit='m/s',
                                      choices=None,
                                      comment=None)]
        message = cantools.db.Message(frame_id=37,
                                      name='message',
                                      length=8,
                                      nodes=['bar'],
                                      signals=signals,
                                      comment='')
        db.add_message(message)
        self.assertEqual(len(db.messages), 1)

    def test_command_line_decode(self):
        argv = ['cantools', 'decode', 'tests/files/socialledge.dbc']
        input_data = """  vcan0  0C8   [8]  F0 00 00 00 00 00 00 00
  vcan0  064   [8]  F0 01 FF FF FF FF FF FF
"""
        expected_output = """  vcan0  0C8   [8]  F0 00 00 00 00 00 00 00 :: SENSOR_SONARS(SENSOR_SONARS_rear: 0.0 , SENSOR_SONARS_right: 0.0 , SENSOR_SONARS_middle: 0.0 , SENSOR_SONARS_left: 0.0 , SENSOR_SONARS_err_count: 15 , SENSOR_SONARS_mux: 0 )
  vcan0  064   [8]  F0 01 FF FF FF FF FF FF :: DRIVER_HEARTBEAT(DRIVER_HEARTBEAT_cmd: 240 )
"""

        stdin = sys.stdin
        stdout = sys.stdout
        sys.argv = argv
        sys.stdin = StringIO(input_data)
        sys.stdout = StringIO()

        try:
            cantools._main()

        finally:
            actual_output = sys.stdout.getvalue()
            sys.stdin = stdin
            sys.stdout = stdout

        self.assertEqual(actual_output, expected_output)


if __name__ == '__main__':
    unittest.main()