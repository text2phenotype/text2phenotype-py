import unittest

from text2phenotype.common.status import StatusReport, Status, Component


class TestStatusReport(unittest.TestCase):
    def test_as_json(self):
        biomed_status = {Component.biomed: (Status.conditional, 'ctakes is not happy')}
        test_target = StatusReport(biomed_status)
        test_target.add_status(Component.ctakes, (Status.dead, 'ctakes is not happy'))
        json_dump = test_target.as_json()
        self.assertEqual((Status.conditional.name, 'ctakes is not happy'), json_dump[Component.biomed.name])
        self.assertEqual((Status.dead.name, 'ctakes is not happy'), json_dump[Component.ctakes.name])
