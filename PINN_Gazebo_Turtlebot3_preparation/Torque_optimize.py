import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import ApplyJointEffort
import threading


class ApplyEffortClient(Node):
    def __init__(self):
        super().__init__('apply_effort_client')
        self.cli = self.create_client(ApplyJointEffort, '/apply_joint_effort')

    def send_effort_request(self, joint_name, effort, start_time_sec, duration_sec):
        request = ApplyJointEffort.Request()
        request.joint_name = joint_name
        request.effort = float(effort)
        request.start_time.sec = start_time_sec
        request.start_time.nanosec = 0
        request.duration.sec = duration_sec
        request.duration.nanosec = 0

        future = self.cli.call_async(request)
        return future


def apply_effort(node, joint_name, effort, start_time, duration):
    """
    施加力矩，并在作用时间结束后施加 0 力矩停止
    """
    node.get_logger().info(f"Applying effort to {joint_name}...")

    future = node.send_effort_request(joint_name, effort, start_time, duration)
    rclpy.spin_until_future_complete(node, future)

    if future.result() is not None:
        node.get_logger().info(f"{joint_name} response: success={future.result().success}, "
                               f"message={future.result().status_message}")

    # 力矩作用完成后，施加 0 力矩
    node.get_logger().info(f"Stopping {joint_name}...")
    stop_future = node.send_effort_request(joint_name, 0, start_time + duration, 1)
    rclpy.spin_until_future_complete(node, stop_future)

    if stop_future.result() is not None:
        node.get_logger().info(f"{joint_name} stop response: success={stop_future.result().success}, "
                               f"message={stop_future.result().status_message}")

    node.get_logger().info(f"{joint_name} effort stopped")


def main(args=None):
    rclpy.init(args=args)
    node = ApplyEffortClient()

    # 左右轮独立的参数
    left_wheel_params = {'joint_name': 'wheel_left_joint', 'effort': 1, 'start_time': 30, 'duration': 2}
    right_wheel_params = {'joint_name': 'wheel_right_joint', 'effort': 1, 'start_time': 30, 'duration': 3}

    # 分别用两个线程控制左右轮，保证它们是独立运行的
    thread_left = threading.Thread(target=apply_effort, args=(node, left_wheel_params['joint_name'], left_wheel_params['effort'], left_wheel_params['start_time'], left_wheel_params['duration']))
    thread_right = threading.Thread(target=apply_effort, args=(node, right_wheel_params['joint_name'], right_wheel_params['effort'], right_wheel_params['start_time'], right_wheel_params['duration']))
    #thread_right = threading.Thread(target=apply_effort, args=(node, **right_wheel_params))

    # 启动线程
    thread_left.start()
    thread_right.start()

    # 等待两个线程执行完成
    thread_left.join()
    thread_right.join()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
