import copy
import os

import numpy as np
import pinocchio as pin
from numpy.linalg import norm

import tsid

print("")
print("Test Task COM")
print("")

pin.switchToNumpyMatrix()

tol = 1e-5
filename = str(os.path.dirname(os.path.abspath(__file__)))
path = filename + '/../../models/romeo'
urdf = path + '/urdf/romeo.urdf'
vector = pin.StdVec_StdString()
vector.extend(item for item in path)
robot = tsid.RobotWrapper(urdf, vector, pin.JointModelFreeFlyer(), False)
model = robot.model()
data = robot.data()

srdf = path + '/srdf/romeo_collision.srdf'
pin.loadReferenceConfigurations(model, srdf, False)
q = model.referenceConfigurations["half_sitting"]

q[2] += 0.84
print("q:", q.transpose())

pin.centerOfMass(model, data, q)

taskCOM = tsid.TaskComEquality("task-com", robot)

Kp = 100 * np.matrix(np.ones(3)).transpose()
Kd = 20.0 * np.matrix(np.ones(3)).transpose()
taskCOM.setKp(Kp)
taskCOM.setKd(Kd)

assert np.linalg.norm(Kp - taskCOM.Kp, 2) < tol
assert np.linalg.norm(Kd - taskCOM.Kd, 2) < tol

com_ref = data.com[0] + np.matrix(np.ones(3) * 0.02).transpose()
traj = tsid.TrajectoryEuclidianConstant("traj_se3", com_ref)
sample = tsid.TrajectorySample(0)

t = 0.0
dt = 0.001
max_it = 1000
Jpinv = np.matrix(np.zeros((robot.nv, 3)))
error_past = 1e100
v = np.matrix(np.zeros(robot.nv)).transpose()

for i in range(0, max_it):
    robot.computeAllTerms(data, q, v)
    sample = traj.computeNext()
    taskCOM.setReference(sample)
    const = taskCOM.compute(t, q, v, data)

    Jpinv = np.linalg.pinv(const.matrix, 1e-5)
    dv = Jpinv * const.vector

    assert np.linalg.norm(Jpinv * const.matrix, 2) - 1.0 < tol
    v += dt * dv
    q = pin.integrate(model, q, dt * v)
    t += dt

    error = np.linalg.norm(taskCOM.position_error, 2)
    assert error - error_past < 1e-4
    error_past = error
    if error < 1e-8:
        print("Success Convergence")
        break
    if i % 100 == 0:
        print("Time :", t, "COM pos error :", error, "COM vel error :", np.linalg.norm(taskCOM.velocity_error, 2))

print("")
print("Test Task Joint Posture")
print("")

q = model.referenceConfigurations["half_sitting"]
q[2] += 0.84

task_joint = tsid.TaskJointPosture("task-posture", robot)

na = robot.nv - 6
Kp = 100 * np.matrix(np.ones(na)).transpose()
Kd = 20.0 * np.matrix(np.ones(na)).transpose()
task_joint.setKp(Kp)
task_joint.setKd(Kd)

assert np.linalg.norm(Kp - task_joint.Kp, 2) < tol
assert np.linalg.norm(Kd - task_joint.Kd, 2) < tol

q_ref = np.matrix(np.random.randn(na)).transpose()
traj = tsid.TrajectoryEuclidianConstant("traj_joint", q_ref)
sample = tsid.TrajectorySample(0)

error_past = 1e100
t = 0.0
max_it = 1000

for i in range(0, max_it):
    robot.computeAllTerms(data, q, v)
    sample = traj.computeNext()
    task_joint.setReference(sample)
    const = task_joint.compute(t, q, v, data)

    Jpinv = np.linalg.pinv(const.matrix, 1e-5)
    dv = Jpinv * const.vector

    assert np.linalg.norm(Jpinv * const.matrix, 2) - 1.0 < tol
    v += dt * dv
    q = pin.integrate(model, q, dt * v)
    t += dt

    error = np.linalg.norm(task_joint.position_error, 2)
    assert error - error_past < 1e-4
    error_past = error
    if error < 1e-8:
        print("Success Convergence")
        break
    if i % 100 == 0:
        print("Time :", t, "Joint pos error :", error, "Joint vel error :",
              np.linalg.norm(task_joint.velocity_error, 2))

print("")
print("Test Task SE3")
print("")

q = model.referenceConfigurations["half_sitting"]
q[2] += 0.84

task_se3 = tsid.TaskSE3Equality("task-se3", robot, "RWristPitch")

na = 6
Kp = 100 * np.matrix(np.ones(na)).transpose()
Kd = 20.0 * np.matrix(np.ones(na)).transpose()
task_se3.setKp(Kp)
task_se3.setKd(Kd)

assert np.linalg.norm(Kp - task_se3.Kp, 2) < tol
assert np.linalg.norm(Kd - task_se3.Kd, 2) < tol

M_ref = pin.SE3.Random()

traj = tsid.TrajectorySE3Constant("traj_se3", M_ref)
sample = tsid.TrajectorySample(0)

t = 0.0
max_it = 1000
error_past = 1e100

for i in range(0, max_it):
    robot.computeAllTerms(data, q, v)
    sample = traj.computeNext()
    task_se3.setReference(sample)

    const = task_se3.compute(t, q, v, data)

    Jpinv = np.linalg.pinv(const.matrix, 1e-5)
    dv = Jpinv * const.vector

    assert np.linalg.norm(Jpinv * const.matrix, 2) - 1.0 < tol

    v += dt * dv
    q = pin.integrate(model, q, dt * v)
    t += dt

    error = np.linalg.norm(task_se3.position_error, 2)
    assert error - error_past < 1e-4
    error_past = error
    if error < 1e-8:
        print("Success Convergence")
        break
    if i % 100 == 0:
        print("Time :", t, "EE pos error :", error, "EE vel error :", np.linalg.norm(task_se3.velocity_error, 2))

print("")
print("Test Task Angular Momentum")
print("")

tol = 1e-5
filename = str(os.path.dirname(os.path.abspath(__file__)))
path = filename + '/../../models/romeo'
urdf = path + '/urdf/romeo.urdf'
vector = pin.StdVec_StdString()
vector.extend(item for item in path)
robot = tsid.RobotWrapper(urdf, vector, pin.JointModelFreeFlyer(), False)
model = robot.model()
data = robot.data()

srdf = path + '/srdf/romeo_collision.srdf'
pin.loadReferenceConfigurations(model, srdf, False)
q = model.referenceConfigurations["half_sitting"]

q[2] += 0.84
print("q:", q.transpose())

taskAM = tsid.TaskAMEquality("task-AM", robot)

Kp = 100 * np.matrix(np.ones(3)).transpose()
Kd = 20.0 * np.matrix(np.ones(3)).transpose()
taskAM.setKp(Kp)
taskAM.setKd(Kd)

assert np.linalg.norm(Kp - taskAM.Kp, 2) < tol
assert np.linalg.norm(Kd - taskAM.Kd, 2) < tol

am_ref = np.matrix(np.zeros(3)).transpose()
traj = tsid.TrajectoryEuclidianConstant("traj_se3", am_ref)
sample = tsid.TrajectorySample(0)

t = 0.0
dt = 0.001
max_it = 1000
Jpinv = np.matrix(np.zeros((robot.nv, 3)))
error_past = 1e100
v = np.matrix(np.random.randn(robot.nv)).transpose()

for i in range(0, max_it):
    robot.computeAllTerms(data, q, v)
    sample = traj.computeNext()
    taskAM.setReference(sample)
    const = taskAM.compute(t, q, v, data)

    # compare the pinocchio method to
    # Del Prete's quick and dirty way to compute drift
    # compute momentum Jacobian at next time step assuming zero acc
    dt = 1e-3
    q_next = pin.integrate(model, q, dt * v)
    data_next = robot.data().copy()
    robot.computeAllTerms(data_next, q_next, v)
    J_am = data.Ag
    J_am_next = data_next.Ag
    drift = (J_am_next[-3:, :] - J_am[-3:, :]) * v / dt
    drift_pin = pin.computeCentroidalMomentumTimeVariation(model, data).angular
    diff_drift = norm(drift_pin - drift)
    print("Difference between drift computations: ", diff_drift)

    Jpinv = np.linalg.pinv(const.matrix, 1e-5)
    dv = Jpinv * const.vector

    assert np.linalg.norm(Jpinv * const.matrix, 2) - 1.0 < tol
    v += dt * dv
    q = pin.integrate(model, q, dt * v)
    t += dt

    error = np.linalg.norm(taskAM.momentum_error, 2)
    assert error - error_past < 1e-4
    error_past = error
    if error < 1e-8:
        print("Success Convergence")
        break
    if i % 100 == 0:
        print("Time :", t, "Momentum error :", error)

print("All test is done")
