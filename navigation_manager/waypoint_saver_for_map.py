import rclpy
from rclpy.node import Node
from pynput import keyboard
import csv
import os
from datetime import datetime
from geometry_msgs.msg import PoseWithCovarianceStamped
import threading

class PoseRecorder(Node):
    def __init__(self):
        super().__init__('pose_recorder')
        self.poses = []
        self.current_pose = None
        self.pose_id = 0
        self.xy_goal_tol_ = 2.0
        self.des_lin_vel_ = 0.4
        self.stop_flag_ = 0
        self.skip_flag_ = 1
        self.gps_pose_enable_ = 0  # Set to 0 as per the new requirement
        self.map_pose_enable_ = 1  # Set to 1 as per the new requirement
        self.init_pose_pub_ = 0

        # Subscribe to /initialpose instead of /odom
        self.create_subscription(PoseWithCovarianceStamped, '/initialpose', self.pose_callback, 10)
        self.pose_publisher = self.create_publisher(PoseWithCovarianceStamped, '/navigation_manager/waypoint_pose', 10) 
        print('Press "q" to quit and save to csv.')

        self.keyboard_thread = threading.Thread(target=self.keyboard_listener)
        self.keyboard_thread.start()

    def pose_callback(self, msg):
        self.current_pose = msg.pose.pose

        # Save the pose whenever it is received from /initialpose
        self.save_current_pose()

    def keyboard_listener(self):
        with keyboard.Listener(on_press=self.on_key_press) as listener:
            listener.join()

    def on_key_press(self, key):
        try:
            if key.char == 'q':
                self.save_poses_to_csv()
                self.destroy_node()
                rclpy.shutdown()
        except AttributeError:
            pass

    def save_current_pose(self):
        if self.current_pose is not None:
            pose_data = [
                str(self.pose_id),
                str(self.current_pose.position.x),
                str(self.current_pose.position.y),
                str(self.current_pose.position.z),
                str(self.current_pose.orientation.x),
                str(self.current_pose.orientation.y),
                str(self.current_pose.orientation.z),
                str(self.current_pose.orientation.w),
                str(self.xy_goal_tol_),
                str(self.des_lin_vel_),
                str(self.stop_flag_),
                str(self.skip_flag_),
                str(self.gps_pose_enable_),
                str(self.map_pose_enable_),
                str(self.init_pose_pub_)
            ]
            self.poses.append(pose_data)
            print('Pose saved! ID: ' + str(self.pose_id))
            self.pose_id += 1
        else:
            print('Warning: No pose received yet.')

    def save_poses_to_csv(self):
        filename = datetime.now().strftime('%Y%m%d%H%M%S') + '_waypoints.csv'
        path = os.path.join(os.path.curdir, 'waypoints', filename)  

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'pos_x', 'pos_y', 'pos_z', 'rot_x', 'rot_y', 'rot_z', 'rot_w', 
                             'xy_goal_tol', 'des_lin_vel', 'stop_flag', 'skip_flag', 'gps_pose_enable', 'map_pose_enable', 'init_pose_pub'])
            writer.writerows(self.poses)

        print(f'Data saved to {path}!')

def main(args=None):
    rclpy.init(args=args)
    pose_recorder = PoseRecorder()

    try:
        rclpy.spin(pose_recorder)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()

