import pandas
from pyscipopt import *
import pandas as pd
from typing import Tuple
import sys
import datetime
from Util.cp_model import cal_arc_jobs_completion
from ortools.sat.python import cp_model
import pandas as pd
import yaml


class IdenticalMachine:
    def __init__(self):
        self.config = None
        self.jobs_df = pd.DataFrame.empty
        self.speeds_df = pd.DataFrame.empty
        self.precedence_df = pd.DataFrame.empty
        self.setup_df = pd.DataFrame.empty
        self.machine_list = []
        self.machines = 0

        self.no_arc_jobs_df = pd.DataFrame.empty
        self.arc_jobs_df = pd.DataFrame.empty

        # used in initial schedules
        self.earliest_start_date_of_no_arc_jobs = 0;
        self.used_machines_of_no_arc_jobs = 0

        self.optimal_value = 0
        self.optimal_solution = []
        self.columns = dict()
        self.master_problem = Model("Master")
        # {machine_key:[schedule_key1,schedule_key2]}
        self.master_vars = {}
        # {machine_key:[[schedule1],[schedule2]}
        self.machine_schedule = {}

    def read_data(self):
        io_begin = datetime.datetime.now();

        file = open(r'config.yaml', 'r', encoding='utf-8')
        file_data = file.read()
        file.close()
        self.config = yaml.load(file_data, Loader=yaml.FullLoader)

        excel_data = pd.read_excel(r"../input/parallel_template.xlsx", sheet_name=None)
        self.jobs_df = excel_data["jobs"]
        self.speeds_df = excel_data["speeds"]
        self.precedence_df = excel_data["precedence"]
        self.setup_df = excel_data["setup"]
        self.machine_list = set(self.speeds_df["machine_id"].tolist())
        self.machines = len(self.machine_list)
        io_end = datetime.datetime.now()
        print("io duration: {0}".format((io_end - io_begin).seconds))

        speed_df = self.speeds_df[["job_id", "speed"]].drop_duplicates()
        self.jobs_df = pd.merge(self.jobs_df, speed_df, how="left", on="job_id")
        self.jobs_df["ratio"] = self.jobs_df.apply(lambda x: x["weight"] / x["speed"], axis=1)

        arc_jobs = set(self.precedence_df["first_job_id"].tolist() + self.precedence_df["second_job_id"].tolist())
        no_arc_jobs = set(self.jobs_df["job_id"].tolist()) - arc_jobs
        self.no_arc_jobs_df = self.jobs_df[self.jobs_df["job_id"].isin(no_arc_jobs)]
        self.no_arc_jobs_df.sort_values(by=["release_date"], ascending=True, inplace=True)
        self.arc_jobs_df = self.jobs_df[self.jobs_df["job_id"].isin(arc_jobs)]

    def guess_initial_max_lateness(self):
        """
            initial guess all job can delay 10%; max_completion =  due_date + max_lateness
        :return:
            max_lateness: the upper bound of Lateness;
            max_completion: dataframe: [job_id,max_completion]
        """
        print("")
        max_lateness = int(self.jobs_df["due_date"].mean() * self.config["initial_max_lateness_ration"])
        max_completion = self.jobs_df[["job_id", "due_date"]]
        max_completion["max_completion"] = max_completion["due_date"].apply(lambda x: x + max_lateness)

        return max_lateness, max_completion

    def initial_no_arc_jobs_completion(self,no_arc_jobs_schedule_df: pandas.DataFrame):
        """
        use all machines, the earliest release job assigning to the earliest available machine ,
         if no machine can do the job, then adding a new machine
        :param no_arc_jobs_schedule_df: a data frame contains job's properties,
              ["job_id","release_date","speed","max_completion",...]
        :return: no_arc_jobs_schedule_df, a data frame ["job_id","machine","start","completion"]
        """
        machine_time_dict = dict(zip(self.machine_list,[0]*self.machines))
        start = []
        completion = []
        machine = []
        for index, row in no_arc_jobs_schedule_df.iterrows():
            machine_id = min(machine_time_dict, key=machine_time_dict.get)
            earliest_time = machine_time_dict[machine_id]
            start_time = max(row["release_date"], earliest_time)
            completion_time = start_time + row["speed"]

            if completion_time <= row["max_completion"]:
                start.append(start_time)
                completion.append(completion_time)
                machine.append(machine_id)
                machine_time_dict.update({machine_id:completion_time})
            else:
                new_machine_id = len(machine_time_dict)
                machine_time_dict.update({new_machine_id:row["release_date"] + row["speed"]})
                start.append(row["release_date"])
                completion.append(row["release_date"] + row["speed"])
                machine.append(new_machine_id)

        no_arc_jobs_schedule_df["start"] = start;
        no_arc_jobs_schedule_df["completion"] = completion;
        no_arc_jobs_schedule_df["machine"] = machine;
        no_arc_jobs_schedule_df = no_arc_jobs_schedule_df[["job_id", "machine", "start", "completion"]]
        return no_arc_jobs_schedule_df

    def initial_arc_jobs_completion(self, arc_jobs_schedule_df: pandas.DataFrame, start_machine_id: int):
        """
        a constraint programming model to get a feasible solution
        :param arc_jobs_schedule_df: a data frame contains job's properties,
              ["job_id","release_date","speed","max_completion",...]
        :param start_machine_id: just to make machine id readable
        :return: arc_jobs_schedule_df, a data frame ["job_id","machine","start","completion"]
        """
        model = cp_model.CpModel()
        solver = cp_model.CpSolver()

        jobs_id = arc_jobs_schedule_df["job_id"].tolist()
        release = dict(zip(jobs_id, arc_jobs_schedule_df["release_date"].tolist()))
        speed = dict(zip(jobs_id, arc_jobs_schedule_df["speed"].tolist()))
        completion = dict(zip(jobs_id, arc_jobs_schedule_df["max_completion"].tolist()))

        start_vars = dict(zip(jobs_id,
                              [model.NewIntVar(release[job], completion[job] - speed[job], "start_{0}".format(job)) for
                               job in jobs_id]))

        for index, row in self.precedence_df.iterrows():
            first_job = row["first_job_id"]
            second_job = row["second_job_id"]
            lower = row["delta_C_lower_bound"]
            upper = row["delta_C_upper_bound"]
            model.Add(
                (start_vars[second_job] + speed[second_job]) - (start_vars[first_job] + speed[first_job]) >= lower)
            model.Add(
                (start_vars[second_job] + speed[second_job]) - (start_vars[first_job] + speed[first_job]) <= upper)

        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("solve")
            completion = [solver.Value(start_vars[job]) + speed[job] for job in jobs_id]
            arc_jobs_schedule_df["completion"] = completion
            arc_jobs_schedule_df["machine"] = [start_machine_id + i + 1 for i in range(len(jobs_id))]
            arc_jobs_schedule_df["start"] = arc_jobs_schedule_df.apply(lambda x: x["completion"]-x["speed"],axis=1)
            arc_jobs_schedule_df = arc_jobs_schedule_df[["job_id", "machine", "start", "completion"]]
            return arc_jobs_schedule_df
        else:
            raise "infeasible precedence constraint"

    def insert_jobs(self, job_id: int, current_start: int, current_completion: int, current_machine: int,
                    to_insert_df_group: pandas.DataFrame.groupby):
        """
        insert a job to some machines, without changing the job's start and completion, just to maintain its precedence
        constraint
        :param job_id: the job_id of to_be_inserted job
        :param current_start: the start_time of to_be_inserted job
        :param current_completion: the completion time of to_be_inserted job
        :param current_machine: the machine of to_be_inserted job
        :param to_insert_df_group: a group by object, key="machine",group_value=["job_id","start","completion"]
        :return: a new machine or its old machine
        """
        for machine, group in to_insert_df_group:
            group_1 = group[(group["completion"] >= current_start) & (group["completion"] <= current_completion)]
            if len(group_1) >= 1:
                continue
            group_2 = group[(group["start"] >= current_start) & (group["start"] <= current_completion)]
            if len(group_2) >= 1:
                continue
            print("=====job {0} can insert into machine {1}".format(job_id, machine))
            return machine
        print("******job {0} can not insert into other machines".format(job_id))
        return current_machine

    def initial_schedules(self, max_completion_df: pandas.DataFrame) -> dict:
        """
            process without constraint jobs and with constraint jobs respectively,
            then do some greedy optimization to combine
        :param max_completion_df: [job_id, completion]
        :return:
            schedules
        """
        no_arc_jobs_schedule_df = pd.merge(self.no_arc_jobs_df, max_completion_df, how="left", on="job_id")
        no_arc_jobs_schedule_df = self.initial_no_arc_jobs_completion(no_arc_jobs_schedule_df)

        arc_jobs_schedule_df = pd.merge(self.arc_jobs_df, max_completion_df, how="left", on="job_id")
        arc_jobs_schedule_df = self.initial_arc_jobs_completion(arc_jobs_schedule_df,
                                                                max(no_arc_jobs_schedule_df["machine"].tolist()))

        to_insert_df_group = no_arc_jobs_schedule_df.groupby("machine")
        arc_jobs_schedule_df["machine"] = arc_jobs_schedule_df.apply(lambda x:
                                                                     self.insert_jobs(x["job_id"],
                                                                                      x["start"],
                                                                                      x["completion"],
                                                                                      x["machine"],
                                                                                      to_insert_df_group),
                                                                     axis=1)
        schedules = no_arc_jobs_schedule_df.append(arc_jobs_schedule_df)
        schedules.to_csv("schedule.csv")
        return schedules

    def solve_problem(self, L_Max, new_jobs_df):
        total_columns = []
        generate_columns = self.initial_schedules(L_Max, new_jobs_df)
        total_columns.append(generate_columns)
        while len(generate_columns) > 0:
            self.solve_RMP(generate_columns)
            generate_columns = self.pricing()
        obj_value, solution = self.branching()
        if obj_value <= self.machines:
            self.optimal_value = obj_value
            self.optimal_solution = solution
        return obj_value, solution

    def run(self):
        # read test input data
        self.read_data()

        # first guess a max_lateness, update each job's due date
        max_lateness, max_completion = self.guess_initial_max_lateness()

        # greedy method to find some initial schedules
        initial_columns = self.initial_schedules(max_completion)

        # # set up model
        # self.model_prepare()
        # obj_value,solution = self.solve_problem(initial_columns, max_completion)
        # if obj_value <= self.machines:
        #     self.L_iteration_mode = -1
        # else:
        #     self.L_iteration_mode = 1
        #
        # # model iteration
        # while True:
        #     if self.L_iteration_mode == -1:
        #         if obj_value >= self.machines:
        #             break
        #     else:
        #         if obj_value <= self.machines:
        #             break
        #     max_lateness, new_jobs_df = self.update_L_Max(max_lateness, self.L_iteration_mode)
        #     initial_columns = self.initial_scheduel(max_lateness, new_jobs_df)
        #     obj_value, solution = self.solve_problem(initial_columns,max_lateness,new_jobs_df)


if __name__ == "__main__":
    identical_model = IdenticalMachine()
    identical_model.run()
