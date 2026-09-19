import json
import unittest
from unittest.mock import patch

from aircard import format_device, get_all_connected_devices, get_connected_device
import aircard_backend


MOCK_RAW_DEVICES = [
    {
        "udid": "00008020-0019086A2E39002E",
        "name": "iPhone测试机",
        "version": "18.7.10",
        "product": "iPhone11,2",
        "language": "zh-Hans-CN",
        "locale": "zh_CN",
        "bold_text": False,
    },
    {
        "udid": "00008150-000A04911A87401C",
        "name": "Z P的iPhone",
        "version": "26.6.2",
        "product": "iPhone18,1",
        "language": "zh-Hans-CN",
        "locale": "zh_CN",
        "bold_text": False,
    },
    {
        "udid": "00008030-001234567890001A",
        "name": "User's iPad",
        "version": "18.1",
        "product": "iPad13,4",
        "language": "en",
        "locale": "en_US",
        "bold_text": True,
    },
    {
        "udid": "00008110-001E50AA0C91401E",
    },
]


class DeviceSelectionTests(unittest.TestCase):
    def test_format_device(self):
        dev = format_device(MOCK_RAW_DEVICES[0])
        self.assertEqual(dev["udid"], "00008020-0019086A2E39002E")
        self.assertEqual(dev["name"], "iPhone测试机")
        self.assertEqual(dev["product"], "iPhone11,2")
        self.assertTrue(dev["connected"])

        # Unpaired device formatting
        unpaired = format_device(MOCK_RAW_DEVICES[3])
        self.assertEqual(unpaired["udid"], "00008110-001E50AA0C91401E")
        self.assertEqual(unpaired["name"], "Locked / Unpaired Device")
        self.assertEqual(unpaired["product"], "")

    @patch("aircard.list_devices", return_value=MOCK_RAW_DEVICES)
    def test_get_all_connected_devices(self, mock_list):
        devices = get_all_connected_devices()
        self.assertEqual(len(devices), 4)
        # Verify iPhones are ordered first, followed by iPad, then unpaired
        self.assertTrue(devices[0]["product"].startswith("iPhone"))
        self.assertTrue(devices[1]["product"].startswith("iPhone"))
        self.assertTrue(devices[2]["product"].startswith("iPad"))
        self.assertEqual(devices[3]["udid"], "00008110-001E50AA0C91401E")

    @patch("aircard.list_devices", return_value=MOCK_RAW_DEVICES)
    def test_get_connected_device_default_and_selection(self, mock_list):
        # Default picks first iPhone
        default_dev = get_connected_device()
        self.assertEqual(default_dev["udid"], "00008020-0019086A2E39002E")

        # Select second device by UDID
        second_dev = get_connected_device("00008150-000A04911A87401C")
        self.assertIsNotNone(second_dev)
        self.assertEqual(second_dev["name"], "Z P的iPhone")
        self.assertEqual(second_dev["udid"], "00008150-000A04911A87401C")

        # Select third device (iPad) by UDID
        ipad_dev = get_connected_device("00008030-001234567890001A")
        self.assertIsNotNone(ipad_dev)
        self.assertEqual(ipad_dev["name"], "User's iPad")

    @patch("aircard.list_devices", return_value=[
        {
            "udid": "wifi-iphone",
            "name": "Wi-Fi iPhone",
            "product": "iPhone18,1",
            "usb": False,
        },
        {
            "udid": "usb-iphone",
            "name": "USB iPhone",
            "product": "iPhone17,1",
            "usb": True,
        },
    ])
    def test_usb_device_preferred_unless_explicitly_selected(self, mock_list):
        self.assertEqual(get_connected_device()["udid"], "usb-iphone")
        self.assertEqual(get_connected_device("wifi-iphone")["udid"], "wifi-iphone")

    @patch("aircard.list_devices", return_value=MOCK_RAW_DEVICES)
    @patch("aircard_backend.find_device_helper", return_value="/bin/device_helper")
    @patch("aircard_backend.native", return_value={"exitCode": 0, "targetGatePassed": True, "operation": {"ok": True}})
    def test_backend_cmd_devices(self, mock_native, mock_helper, mock_list):
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            aircard_backend.cmd_devices("00008150-000A04911A87401C")

        output = json.loads(f.getvalue().strip())
        self.assertTrue(output["connected"])
        self.assertEqual(len(output["devices"]), 4)
        self.assertEqual(output["selected_udid"], "00008150-000A04911A87401C")
        self.assertEqual(output["device"]["name"], "Z P的iPhone")
        self.assertTrue(output["device"]["airlift_compatible"])


if __name__ == "__main__":
    unittest.main()
