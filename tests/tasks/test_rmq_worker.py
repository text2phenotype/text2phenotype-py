import concurrent.futures
from unittest import TestCase
from unittest.mock import (
    MagicMock,
    patch,
    PropertyMock,
)
from uuid import uuid4

import pika
from pika import BasicProperties

from text2phenotype.constants.environment import Environment
from text2phenotype.tasks.document_info import DocumentInfo
from text2phenotype.tasks.job_task import JobTask
from text2phenotype.tasks.mixins import RedisMethodsMixin
from text2phenotype.tasks.rmq_worker import (
    RMQConsumerTaskWorker,
    RMQConsumerWorker,
)
from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskStatus,
    WorkType,
)
from text2phenotype.tasks.task_info import (
    DrugModelTaskInfo,
    TaskInfo,
)
from text2phenotype.tasks.task_message import TaskMessage
from text2phenotype.tasks.work_tasks import (
    ChunkTask,
    DocumentTask,
)


class Worker(RMQConsumerWorker):
    def do_work(self):
        pass


class TestRMQConsumerWorker(TestCase):
    def setUp(self) -> None:
        self.worker = Worker()

        self.deliver = pika.spec.Basic.Deliver(delivery_tag=1)
        self.props = BasicProperties()
        self.body = TaskMessage().json().encode()

        self.future = concurrent.futures.Future()
        setattr(self.future, 'deliver', self.deliver)
        setattr(self.future, 'message', self.body.decode())
        self.future.set_running_or_notify_cancel()

    def test_on_message(self):
        with patch.object(RMQConsumerWorker, 'on_process_done') as on_process_done:
            future = self.worker.on_message(pika.spec.Channel(), self.deliver, self.props, self.body)
            future.result()

            # Check job-result handler's call
            on_process_done.assert_called_once_with(future)

            # Check important stuff for the job-result handler
            self.assertEqual(getattr(future, 'deliver', None), self.deliver)
            self.assertEqual(getattr(future, 'message', None), self.body.decode())

            self.assertIn(future, self.worker.futures)

    def test_successful(self):
        with patch('text2phenotype.tasks.rmq_worker.RMQConsumerWorker.accept') as accept:
            self.future.set_result(None)
            self.worker.on_process_done(self.future)
            accept.assert_called_once_with(1)

    def test_validation_error(self):
        with patch('text2phenotype.tasks.rmq_worker.RMQConsumerWorker.reject') as reject:
            self.future.set_exception(ValueError('my error'))
            self.worker.on_process_done(self.future)
            reject.assert_called_once_with(1)

    def test_exception(self):
        try:
            TaskMessage.from_json('')
        except Exception as err:
            self.future.set_exception(err)

        with patch('text2phenotype.tasks.rmq_worker.RMQConsumerWorker.requeue') as requeue:
            self.worker.on_process_done(self.future)
            requeue.assert_called_once_with(1)

        with patch('text2phenotype.tasks.rmq_worker.RMQConsumerWorker.reject') as reject:
            self.future.deliver.redelivered = True
            self.worker.on_process_done(self.future)
            reject.assert_called_once_with(1)


class DrugModelWorker(RMQConsumerTaskWorker):
    TASK_TYPE = TaskEnum.drug
    WORK_TYPE = WorkType.chunk

    def do_work(self) -> TaskInfo:
        return DrugModelTaskInfo()


class TestRMQConsumerTaskWorker(TestCase):

    def setUp(self) -> None:
        self.worker = DrugModelWorker()
        self.worker.task_message = TaskMessage(work_type=WorkType.chunk)
        self.job_task = JobTask(job_id=uuid4().hex)
        self.doc_task = DocumentTask(
            document_info=DocumentInfo(
                document_id=uuid4().hex,
                source='',
                tid='',
            ),
        )

        initial_task_message_patch = patch.object(DrugModelWorker, 'initial_task_message', new_callable=PropertyMock)
        initial_task_message_patch = initial_task_message_patch.start()
        initial_task_message_patch.return_value = TaskMessage(work_type=WorkType.chunk)

        self.task_info_patch = patch.object(DrugModelWorker, 'task_info', new_callable=PropertyMock).start()
        self.task_info_patch.return_value = DrugModelTaskInfo()

        self.get_job_task_patch = patch.object(DrugModelWorker, 'get_job_task').start()
        self.get_job_task_patch.return_value = self.job_task

        self.get_document_task_patch = patch.object(DrugModelWorker, 'get_document_task').start()
        self.get_document_task_patch.return_value = self.doc_task

        self.do_work_patch = patch.object(DrugModelWorker, 'do_work').start()
        self.do_work_patch.return_value = DrugModelTaskInfo()

        self.work_task_patch = patch.object(DrugModelWorker, 'work_task', new_callable=PropertyMock).start()
        self.work_task_patch.return_value = ChunkTask(
            job_id=self.job_task.job_id,
            document_id=self.doc_task.document_id,
            task_statuses={
                TaskEnum.drug: DrugModelTaskInfo(),
            },
            chunk_num=1,
            chunk_size=1000,
            text_span=[],
        )

        init_work_task_patch = patch.object(DrugModelWorker, 'init_work_task').start()
        refresh_work_task_patch = patch.object(DrugModelWorker, 'refresh_work_task').start()
        save_work_task_patch = patch.object(DrugModelWorker, 'save_work_task').start()
        redis_patch = patch('text2phenotype.tasks.mixins.RedisClient').start()

        self.addCleanup(
            initial_task_message_patch.stop,
            init_work_task_patch.stop,
            self.task_info_patch.stop,
            self.get_job_task_patch.stop,
            self.get_document_task_patch.stop,
            refresh_work_task_patch.stop,
            save_work_task_patch.stop,
            self.do_work_patch.stop,
            self.work_task_patch.stop,
            redis_patch.stop,
        )

    def test_on_message(self):
        deliver = pika.spec.Basic.Deliver(delivery_tag=1)
        props = BasicProperties()
        body = TaskMessage(work_type=WorkType.chunk).json().encode()

        with patch.object(RMQConsumerTaskWorker, 'on_process_done') as on_process_done:
            future = self.worker.on_message(pika.spec.Channel(), deliver, props, body)
            future.result()

            # Check job-result handler's call
            on_process_done.assert_called_once_with(future)

            # Check important stuff for the job-result handler
            self.assertEqual(getattr(future, 'deliver', None), deliver)
            self.assertEqual(getattr(future, 'message', None), body.decode())

            self.assertIn(future, self.worker.futures)

    def test_process_task_message_exception(self):
        with self.assertRaises(Exception):
            self.worker.task_message = TaskMessage()
            self.worker.process_message()

        with self.assertRaises(Exception):
            self.worker.task_message = TaskMessage(work_type=WorkType.document)
            self.worker.process_message()

    def test_process_task_message_successful(self):
        previous_task_info = self.worker.task_info.copy(deep=True)

        self.worker.process_message()

        actual_task_info = self.worker.work_task.task_statuses[TaskEnum.drug]
        self.assertEqual(TaskStatus.completed_success, actual_task_info.status)
        self.assertEqual(1, self.worker.task_info.attempts)

        # check than fields were updated
        self.assertNotEqual(previous_task_info.started_at, self.worker.task_info.started_at)

    def test_process_task_message_work_task_not_found(self):
        self.work_task_patch.return_value = None

        self.worker.process_message()

        self.do_work_patch.assert_not_called()

    def test_process_task_message_completed_task(self):
        self.task_info_patch.return_value = DrugModelTaskInfo(
            status=TaskStatus.completed_success,
        )

        self.worker.process_message()

        self.do_work_patch.assert_not_called()

    def test_process_task_message_attempts_exceeded(self):
        attempts = Environment.RETRY_TASK_COUNT_MAX.value + 1
        self.task_info_patch.return_value = DrugModelTaskInfo(attempts=attempts)

        with patch.object(RedisMethodsMixin, 'task_update_manager') as task_update_manager:
            task_update_manager.return_value.__enter__ = MagicMock(return_value=self.doc_task)
            self.worker.process_message()

        self.do_work_patch.assert_not_called()
        self.assertEqual(self.worker.task_info.status, TaskStatus.completed_failure)
        self.assertEqual(self.worker.task_info.attempts, attempts + 1)
        self.assertTrue(self.worker.task_info.error_messages)

    def test_process_task_message_canceled_job(self):
        self.job_task.user_canceled = True
        self.get_job_task_patch.return_value = self.job_task

        self.worker.process_message()

        self.do_work_patch.assert_not_called()
        self.assertEqual(self.worker.task_info.status, TaskStatus.canceled)
        self.assertEqual(self.worker.task_info.attempts, 1)

    def test_process_task_message_exception_during_do_work(self):
        expected_exception = Exception('Some exception happened')
        self.do_work_patch.side_effect = expected_exception

        self.worker.process_message()

        self.assertEqual(self.worker.task_info.status, TaskStatus.failed)
        self.assertIn(repr(expected_exception), self.worker.task_info.error_messages)

    def test_process_task_message_stop_documents_on_failure_true(self):
        self.doc_task.failed_tasks.append(TaskEnum.lab)
        self.get_document_task_patch.return_value = self.doc_task

        self.job_task.stop_documents_on_failure = True
        self.get_job_task_patch.return_value = self.job_task

        self.worker.process_message()

        self.do_work_patch.assert_not_called()
        self.assertEqual(self.worker.task_info.status, TaskStatus.canceled)
        self.assertEqual(self.worker.task_info.attempts, 1)

    def test_process_task_message_stop_documents_on_failure_false(self):
        self.doc_task.failed_tasks.append(TaskEnum.lab)
        self.get_document_task_patch.return_value = self.doc_task

        self.job_task.stop_documents_on_failure = False
        self.get_job_task_patch.return_value = self.job_task

        self.do_work_patch.return_value = DrugModelTaskInfo()

        self.worker.process_message()

        self.do_work_patch.assert_called_once()
        self.assertEqual(TaskStatus.completed_success, self.worker.work_task.task_statuses[TaskEnum.drug].status)
        self.assertEqual(1, self.worker.task_info.attempts)

    def test_send_back_to_sequencer(self):
        message = TaskMessage(work_type=WorkType.chunk, redis_key='Test Key')
        deliver = pika.spec.Basic.Deliver(delivery_tag=1)

        with self.subTest('After exception'):
            future = concurrent.futures.Future()
            future.set_exception(ValueError('my error'))
            setattr(future, 'message', message.json())
            setattr(future, 'deliver', deliver)
            with patch('text2phenotype.tasks.rmq_worker.RMQConsumerWorker.on_process_done') as on_process_done:
                with patch.object(DrugModelWorker, 'publish_message') as publish_message:
                    self.worker.on_process_done(future)

                    on_process_done.assert_called_once_with(future)
                    publish_message.assert_not_called()

        with self.subTest('Success result'):
            future = concurrent.futures.Future()
            future.set_result(None)
            setattr(future, 'message', message.json())
            setattr(future, 'deliver', deliver)
            with patch('text2phenotype.tasks.rmq_worker.RMQConsumerWorker.on_process_done') as on_process_done:
                with patch.object(DrugModelWorker, 'publish_message') as publish_message:
                    self.worker.on_process_done(future)

                    on_process_done.assert_called_once_with(future)
                    publish_message.assert_called_once_with(Environment.SEQUENCER_QUEUE.value, message)
