# parallel machine scheduling
***
##1.introduction
   - generalization of the single machine
   - special case of flow shop
   - decomposition procedures for multistage systems
<br>

##2. the makespan without preemption: **$P_m$||$C_{max}$**
   - ***LPT(longest process time first) rule*** : yield a good bound, not optimal *<u>(page95)</u>*
   - ***LFJ(least flexible job fist) rule***: optimal for **$P_m$| $p_j=1$,$M_j$ | $C_{max}$** *<u>(page103)</u>*
<br>    
##3. the makespan with preemption
   - ***An optimal algorithm: more practical in practise*** *<u>(page106)</u>*
   - ***LRPT largest remaining process time fist***: optimal rule for discrete time and continues time  **$P_m$|$r_j$, $prmp$ |$C_{max}$**(可以指定一个整数的时间间隔来切换，得到方案后再重新整理，使方案更合理)*<u>(page108)</u>*
   - ***LRPT-FM largest remaining process time fist to the fast machine***: optimal rule for discrete time and continues time **$Q_m$| $r_j$,$prmp$ |$C_{max}$** (可以指定一个整数的时间间隔来切换，得到方案后再重新整理，使方案更合理)*<u>(page111)</u>*
  <br>
##4. the total  completion time without preemptions
- ***SPT shortest process time first rule*** : optimal for both **$P_m$||$\sum$$C_j$ and 1||$\sum$$C_j$** *<u>(page112)</u>*
- ***WSPT weight shortest process time first rule*** : optimal for  **1||$\sum$$w_j$$C_j$**, but not optimal for **$P_m$||$\sum$$w_j$$C_j$** *<u>(page113)</u>*
<br>
##5. the total completion time with preemptions
   - ***SPT shortest process time first rule***： optimal for **$P_m$| $prmp$ |$\sum$$C_j$** *<u>(page116)</u>*
   - ***SRPT-FM shortest remian process time with fast machine first rule***： optimal for **$Q_m$| $prmp$ |$\sum$$C_j$** *<u>(page117)</u>*


## 6. *a column generation approach*  for $R_m$|$r_j$,$d_j$,$prec$|$L_{max}$ [1]

- solution procedure

``` mermaid
flowchart TB

    begin(start) -->initial_L[[to get start:initial an L' for L_max ]]
    style begin fill:#f9f,stroke:#333,stroke-width:4px

    initial_L-->|L'|update[L_max=L', refresh job's duedate]
    update -->|L_max,duedate|initial_column[[columns initialization strategy]]
    initial_column--->|initial columns| solve_relax_rmp[solve relax rmp: a set partition model]

    solve_relax_rmp--->|dual multipliers|local_search[[local search pricing: 2 step heuristic]]

    local_search--->can_find_entering_column{has nagetive reduced cost columns?}
    can_find_entering_column--->|Yes|add_columns[[columns selection strategy]]
    add_columns--->|add new columns|solve_relax_rmp
    can_find_entering_column--->|No| solve_price_ilp[[ilp pricing: use lowbound as constraint and find a feasibile soluion]]
    solve_price_ilp--->has_feasible_solution{has feasibile solution?}
    has_feasible_solution--->|Yes|add_columns
    has_feasible_solution--->|No|current_relax_rmp_obj{current_relax_rmp_obj >= M ?}
    current_relax_rmp_obj--->|Yes|relax_rmp_dequeue[dequeue from Q]
    current_relax_rmp_obj--->|No|record_current_relax_model[[record current relax model in a queue Q]]
    record_current_relax_model--->decrease[L' = L'-1]
    decrease--->|L'|update
    

    relax_rmp_dequeue-->branching[[brancing:pass the relax rmp obj and solve an ILP]]
    
    branching--->branching_result{the integer obj value <= M? or Q is empty}
    branching_result---->|No|relax_rmp_dequeue
    branching_result---->|Yes| out_put_result[output current best result as optimal result or report no solution found]
    out_put_result--->finish(end)
    style finish fill:#f9f,stroke:#333,stroke-width:4px
  
```
- initial column strategy: 
  ``` mermaid
   flowchart TB
      subgraph initial
         direction LR
         job_type[select jobs with arc in set arcs, otherwise in set noarcs]
         job_type--->machine[add one machine to set machines]
      end
      subgraph addarcjob
         direction LR
         arc_dequeue[pick an arc]
         arc_dequeue-->arcjob_insert[ place job to the first machine of machine_set which can commodate the job ]
         arcjob_insert--->arcjob_cond1{add job success?}
         arcjob_cond1--->|Yes|arcjob_record[mark job's C]-->arcjob_cond2{all arc finished?}
         arcjob_cond1--->|No| add_machine[add a new machine to machine_set, place job to machine]--->arcjob_record
         arcjob_cond2--->|Yes|add_arc_job[add arc job finish]
         arcjob_cond2--->|No|arc_dequeue
      end
      subgraph addnoarcjob
         direction LR
         job_dequeue[pick an job]
         job_dequeue-->job_insert[ place job to the first machine of machine_set which can commodate the job ]
         job_insert--->job_cond1{add job success?}
         job_cond1--->|Yes|job_record[mark job's C]-->job_cond2{all arc finished?}
         job_cond1--->|No| add_job_machine[add a new machine to machine_set, place job to machine]--->job_record
         job_cond2--->|Yes|add_noarc_job[add no arc job finish]
         job_cond2--->|No|job_dequeue
      end

      begin(start)-->initial
      initial-->addarcjob
      addarcjob--->addnoarcjob
      addnoarcjob--->finish(end)
  ```

- local search
  ```mermaid
   flowchart TB
   begin(start)-->initial[random select jobs]
   initial-->rank_jobs[step1 method cal reduced cost for selct jobs]
   rank_jobs-->negative{is_nagetive?}
   negative--->|Yes| add[add jobs to columns]
   negative --->|No| step2[apply step2 methond] 
   add--->step2--->step1[step1 method cal reduced cost for new jobs]
   step1--->enough[until colums size == 50]
   enough--->finishe(end)

  ```
## reference:
[1] Using column generation to solve parallel machine scheduling problems with minmax objective functions
[2] Parallel machine scheduling by column generation
[3] A linear programming and constraint propagation-based lower bound for the RCPSP
