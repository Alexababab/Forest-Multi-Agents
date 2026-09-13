const scenes = [
  {
    id: 1,
    label: 'SCENE 01 · 密林线廊',
    hud: 'DENSE FOREST · LINE CORRIDOR',
    title: '密林 + 纵向线状设施',
    shortTitle: '密林线廊场景',
    healthTitle: '成熟密林 · 高郁闭度',
    coverage: 99.5,
    green: '中高', greenBar: 82,
    shadow: '25%', shadowBar: 25,
    health: 88,
    riskLevel: '中高风险',
    primaryRisk: '线廊林火 · 生境切割',
    observation: '冠层极密且连续，线状设施纵向贯穿林地，建议关注线廊火险与栖息地切割。',
    vegetation: '植被覆盖度约 99.5%，冠层极密、阴影占比约 25%，属高郁闭度成熟林，整体林分完整、绿度中等偏上。线状设施纵向贯穿林左，对连续林冠形成切割。',
    overview: '当前影像为高郁闭度成熟林场景，冠层连续，左侧存在纵向线状设施，对林冠形成局部切割。',
    riskIntro: '线缆下方植被过高与高郁闭林分叠加，建议优先纳入巡护与清障复核。',
    risks: [
      ['线廊林火', '高'], ['生态廊道割裂', '中高'], ['高郁闭结构火险', '中高']
    ],
    riskText: '重点关注线廊林火风险、连续栖息地切割及高郁闭林分火险叠加。',
    actions: [
      ['线树清障', '建立线树安全距离清障带，定期修剪廊下超高植被。'],
      ['生态缓冲', '线缆两侧设置低矮灌木型生态友好缓冲带。'],
      ['网格巡护', '将线廊纳入森林火险网格化巡护与重点巡检。'],
      ['智能监测', '增设可见光 / 热红外监控，强化早期异常发现。']
    ],
    actionText: '建议建立线树安全距离清障带，设置生态友好缓冲带，并将线廊纳入森林火险网格化巡护与热红外监控。',
    trace: ['scene elements extracted · canopy / corridor / shadow','cover=99.5% · canopy density=high','fire corridor ↑ · habitat fragmentation ↑','clearance buffer / patrol grid / thermal monitoring']
  },
  {
    id: 2,
    label: 'SCENE 02 · 干草绿斑',
    hud: 'DRY GRASSLAND · GREEN PATCHES',
    title: '干草地 + 绿斑 + 团状树冠',
    shortTitle: '干草绿斑场景',
    healthTitle: '草地主导 · 活力一般',
    coverage: 78.8,
    green: '偏低', greenBar: 42,
    shadow: '较少', shadowBar: 18,
    health: 61,
    riskLevel: '中高风险',
    primaryRisk: '草地退化 · 旱化',
    observation: '浅褐干草与裸斑明显，鲜绿斑块零散，需关注水分胁迫、踩踏过载与灌丛扩张。',
    vegetation: '植被覆盖度约 78.8%（六图中最低），mean_green 偏低（21.0），浅褐干草占比大、鲜绿斑块与团状树冠零星散布，呈草地主导、灌丛/疏林点缀景观；绿度活力一般，存在明显枯黄/裸地信号。',
    overview: '当前影像以干草地为主，鲜绿斑块和团状树冠零星散布，可见明显枯黄与低覆盖区域。',
    riskIntro: '大面积干枯草本与裸斑提示水分胁迫或放牧 / 踩踏过载，旱季同时存在火险上升。',
    risks: [['草地退化 / 旱化','高'],['灌丛入侵','中'],['旱季火险','中高']],
    riskText: '重点关注草地退化/旱化、灌丛侵占及旱季干草可燃物累积带来的火险。',
    actions: [
      ['草畜平衡', '核定载畜量，实行轮牧 / 休牧并建立监测样地。'],
      ['灌草监测', '动态监测灌草比例，必要时开展机械平茬等恢复措施。'],
      ['封育补播', '补播耐旱乡土草种，针对低覆盖区实施封育恢复。'],
      ['物候序列', '建立返青期 / 枯黄期多时相遥感监测序列。']
    ],
    actionText: '建议开展草畜平衡监测、轮牧休牧、灌草比例动态监测，并通过封育补播及多时相物候遥感持续跟踪恢复。',
    trace: ['dry grass / bare patches / shrubs extracted','cover=78.8% · mean_green=21.0','degradation ↑ · drought ↑ · dry-season fire ↑','rotation grazing / reseeding / phenology monitoring']
  },
  {
    id: 3,
    label: 'SCENE 03 · 斑驳冠层',
    hud: 'MOTTLED CANOPY · PALE CROWNS',
    title: '斑驳森林树冠（右上浅色树冠）',
    shortTitle: '斑驳冠层场景',
    healthTitle: '连续冠层 · 局部色泽异常',
    coverage: 100,
    green: '中高', greenBar: 78,
    shadow: '9.2%', shadowBar: 9.2,
    health: 79,
    riskLevel: '中风险',
    primaryRisk: '病虫害 · 冠层褪绿',
    observation: '冠层连续但斑驳明显，右上浅色树冠群与周边深绿形成色差，建议开展地面抽样核查。',
    vegetation: '植被覆盖度约 100%，阴影占比约 9.2%（偏低），冠层连续但斑驳明显；右上区域出现白绿色/浅色树冠群，与周边深绿形成色差，提示局部树冠色泽异常或物候差异。',
    overview: '当前影像冠层连续但明暗斑驳，右上区域存在明显浅色树冠群，适合作为冠层异常复核样本。',
    riskIntro: '局部浅色冠层可能对应病虫害、干旱褪绿或物候差异，若呈扩散趋势需重点关注林分健康下降。',
    risks: [['病虫害 / 衰退','中高'],['冠层褪绿扩散','中'],['次期害虫条件','中']],
    riskText: '重点关注局部浅色冠层可能对应的病虫害、干旱褪绿或林分衰退，并持续观察异常区域是否扩散。',
    actions: [
      ['地面核查', '对浅色冠层区重点抽样，区分物候差异与病虫害。'],
      ['红边识别', '结合多时相 Sentinel-2 红边 NDVI 建立识别模型。'],
      ['精准防控', '确认为病虫害后及时施药 / 诱捕 / 清理枯死木。'],
      ['相邻检疫', '加强相邻林区巡查检疫，阻断潜在传播路径。']
    ],
    actionText: '建议优先开展浅色冠层地面核查，并结合多时相红边 NDVI 建立异常识别；若确认病虫害则实施精准防控与相邻林区检疫。',
    trace: ['mottled canopy / pale crowns extracted','cover=100% · shadow=9.2%','pest-or-decline signal ↑ · spread watch','field sampling / red-edge NDVI / targeted control']
  },
  {
    id: 4,
    label: 'SCENE 04 · 草灌交错',
    hud: 'GRASS-SHRUB MOSAIC · TRAIL TRACE',
    title: '草地灌丛 + 树冠阴影 + 浅色细线',
    shortTitle: '草灌交错场景',
    healthTitle: '低矮草灌 · 冠层开阔',
    coverage: 99.9,
    green: '中等', greenBar: 64,
    shadow: '6.2%', shadowBar: 6.2,
    health: 80,
    riskLevel: '中风险',
    primaryRisk: '人为扰动 · 土壤压实',
    observation: '草本层占优、散生乔木明显，浅色线状痕迹疑似人为步道，需核查踩踏与游憩干扰。',
    vegetation: '植被覆盖度约 99.9%，阴影占比仅 6.2%（六图中最低），以低矮草地/灌丛为主、冠层开阔；树冠投下圆形阴影说明存在散生乔木，绿度中等（38.2），植被以草本层占优。',
    overview: '当前影像为开阔草地 / 灌丛与散生乔木混合场景，局部浅色细线疑似人为进入路径。',
    riskIntro: '浅色细线可能对应游憩、放牧或违规进入路径，长期可能演变为裸径扩张和土壤压实。',
    risks: [['人为活动踪迹','中高'],['林草交错脆弱性','中'],['水土保持偏弱','中']],
    riskText: '重点关注浅色线状痕迹所代表的人为扰动、裸径扩张与土壤压实，以及开阔林草交错带的生态脆弱性。',
    actions: [
      ['路径核查', '核查浅色线状痕迹是否为违规步道或踩踏路径。'],
      ['生态封育', '对受扰动路径实施封育和植被恢复，控制裸径扩张。'],
      ['大树保护', '保护散生大树，维持重要栖息地与种源功能。'],
      ['承载监管', '将开阔地纳入访客承载量与生态红线监管。']
    ],
    actionText: '建议核查浅色路径并对违规进入区域实施生态封育与植被恢复，同时保护散生大树并加强自然保护地访客承载与扰动强度监管。',
    trace: ['grass-shrub / scattered trees / trail extracted','cover=99.9% · shadow=6.2%','human disturbance ↑ · soil compaction watch','trail closure / revegetation / visitor load control']
  },
  {
    id: 5,
    label: 'SCENE 05 · 浓密森林',
    hud: 'DENSE CANOPY · HIGH GREENNESS',
    title: '浓密森林冠层（高绿度）',
    shortTitle: '浓密森林场景',
    healthTitle: '成熟密林 · 高绿度',
    coverage: 100,
    green: '高', greenBar: 90,
    shadow: '7%', shadowBar: 7,
    health: 93,
    riskLevel: '中高风险',
    primaryRisk: '高郁闭火险 · 结构单一',
    observation: '冠层连续、绿度高、整体健康，但高郁闭结构需关注火势快速蔓延与单一林分抗扰动不足。',
    vegetation: '植被覆盖度 100%，mean_green 44.4（六图中第二高），属绿度高、活力旺盛的成熟密林，冠层连续、郁闭良好（阴影 7%），整体森林健康状态佳。',
    overview: '当前影像为高绿度成熟密林，冠层连续且整体健康，是典型的高郁闭林分样本。',
    riskIntro: '连续高郁闭冠层一旦起火蔓延快，若树种结构单一还可能存在抗病虫害与抗灾韧性不足。',
    risks: [['纯林 / 高郁闭火险','高'],['单一结构韧性不足','中高'],['林分密度过高','中']],
    riskText: '重点关注高郁闭密林火势快速蔓延、单一结构抗扰动韧性不足以及林分密度偏高等结构性风险。',
    actions: [
      ['火险阻隔', '维护防火线与生物防火林带，强化重点火险区管理。'],
      ['早期监测', '配置烟感 / 热成像监测，提高早期发现能力。'],
      ['结构经营', '开展目标树抚育和间伐，形成复层异龄混交林。'],
      ['健康指数', '建立森林健康指数 FHI 长时序遥感监测。']
    ],
    actionText: '建议纳入重点火险区并维护防火阻隔带，配置早期烟感 / 热成像监测，同时通过目标树抚育、间伐和 FHI 长时序监测提升抗灾韧性。',
    trace: ['dense canopy / high greenness extracted','cover=100% · mean_green=44.4','crown fire spread ↑ · resilience watch','firebreak / thinning / FHI time-series monitoring']
  },
  {
    id: 6,
    label: 'SCENE 06 · 健康林窗',
    hud: 'HEALTHY FOREST · CANOPY GAPS',
    title: '斑驳森林树冠（明暗交错）',
    shortTitle: '健康林窗场景',
    healthTitle: '结构丰富 · 活力最佳',
    coverage: 100,
    green: '最高', greenBar: 96,
    shadow: '12%', shadowBar: 12,
    health: 96,
    riskLevel: '低—中风险',
    primaryRisk: '极端天气 · 林窗结构',
    observation: '绿度活力六图最高，冠层明暗交错、层次丰富，整体健康，风险主要来自林窗结构与极端天气。',
    vegetation: '植被覆盖度 100%，mean_green 45.9（六图最高），绿度活力最佳；阴影占比 12%，冠层斑驳、亮绿与深绿交错，属结构丰富、层次分明的健康森林，林分生产力高。',
    overview: '当前影像为结构丰富的健康森林，亮绿与深绿树冠交错、林窗明显，整体生产力与活力较高。',
    riskIntro: '整体状态优良，主要关注林窗与冠层高差在大风、暴雨等极端天气下引发的风倒 / 折枝风险。',
    risks: [['林窗风倒 / 折枝','中'],['林下可燃物累积','中'],['游憩承载超限','低—中']],
    riskText: '整体生态状态优良，主要为结构性风险：林窗与冠层高差可能提高风倒 / 折枝概率，同时仍需关注林下可燃物与游憩承载。',
    actions: [
      ['固定样方', '作为质量标杆样地，建立固定监测样方并跟踪 NDVI。'],
      ['近自然经营', '林窗区域补植乡土阔叶树种，维持异龄复层结构。'],
      ['生物多样性', '保留枯立木 / 倒木，强化栖息地与多样性保育。'],
      ['适度修枝', '仅对高风险林缘 / 林窗进行适度修枝和加固。']
    ],
    actionText: '建议将其作为森林生态质量标杆样地，开展固定样方与 NDVI 长期跟踪；林窗区域采用近自然经营并保留枯立木 / 倒木，仅对高风险林缘适度修枝。',
    trace: ['mixed canopy / gaps / vertical structure extracted','cover=100% · mean_green=45.9','windthrow structure watch · fuel accumulation','fixed plots / near-natural management / NDVI tracking']
  }
];

let currentScene = 0;
let customImage = null;
let currentImageFile = null;

const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];

const dom = {
  header: $('#siteHeader'), progress: $('#pageProgress'), mainImage: $('#mainImage'), sceneLabel: $('#currentSceneLabel'), hud: $('#hudScene'), taskObservation: $('#taskObservation'),
  scan: $('#scanOverlay'), coverage: $('#coverageValue'), coverageBar: $('#coverageBar'), green: $('#greenValue'), greenBar: $('#greenBar'), shadow: $('#shadowValue'), shadowBar: $('#shadowBar'),
  healthScore: $('#healthScore'), statusGlyphLabel: $('#statusGlyphLabel'), healthRing: $('#healthRing'), healthTitle: $('#healthTitle'), vegetationText: $('#vegetationText'), overallRisk: $('#overallRisk'), primaryRisk: $('#primaryRisk'), riskIntro: $('#riskIntro'), riskList: $('#riskList'), actionList: $('#actionList'),
  reportSceneName: $('#reportSceneName'), reportNo: $('#reportNo'), paperCode: $('#paperCode'), paperSceneTitle: $('#paperSceneTitle'), reportStatus: $('#reportStatus'), paperStatus: $('#paperStatus'), exportReport: $('#exportReport'), reportOverview: $('#reportOverview'), reportVegetation: $('#reportVegetation'), reportRisk: $('#reportRisk'), reportAction: $('#reportAction'),
  agentTrace: $('#agentTrace'), analysisStateText: $('#analysisStateText'), analysisStateDot: $('#analysisStateDot'), taskProgress: $('#taskProgress'), analysisPrompt: $('#analysisPrompt'), currentFileName: $('#currentFileName'), runButton: $('#runAnalysis')
};

const agentRoles = ['planner','executor','vision','knowledge','critic','finalizer'];
let stageProgress = 0;
let sseRunFinished = false;
let sseErrorSeen = false;
let isAnalyzing = false;
let evidenceCount = 0;
let latestFinalReport = '';
const workflowStages = ['planner','vision','knowledge','critic','finalizer'];
const workflowStageIndex = Object.fromEntries(workflowStages.map((s,i)=>[s,i]));
let currentWorkflowStage = 'planner';
let workflowStageStates = Object.fromEntries(workflowStages.map(s=>[s,'waiting']));
function setAgentState(role, state, label){
  const card = document.querySelector(`[data-role="${role}"]`);
  if(!card) return;
  card.dataset.state = state || 'waiting';
  const status = card.querySelector('[data-agent-status]');
  if(status) status.textContent = label || ({waiting:'等待任务',active:'运行中',completed:'已完成',replan:'需要重新规划',failed:'失败'}[state] || '等待任务');
}
function resetAgentStates(){ agentRoles.forEach(role=>setAgentState(role,'waiting')); }
function setAnalysisStatus(state, title, detail){
  dom.analysisStateText.textContent = title;
  dom.analysisStateDot.dataset.state = state;
  dom.taskObservation.textContent = detail;
}

function setWorkflowStage(stage, state, description, progress){
  const index = workflowStageIndex[stage];
  if(index === undefined) return;
  currentWorkflowStage = stage;
  workflowStageStates[stage] = state;
  const criticCurrent = stage === 'critic' && (state === 'active' || state === 'replan');
  if(modalCard) modalCard.classList.toggle('critic-current', criticCurrent);
  modalSteps.forEach((el,i)=>{
    const stageState = workflowStageStates[workflowStages[i]];
    el.classList.toggle('active', stageState === 'active');
    el.classList.toggle('done', stageState === 'completed');
    el.classList.toggle('replan', stageState === 'replan');
    el.classList.toggle('failed', stageState === 'failed');
  });
  if(description) modalText.textContent = description;
  if(typeof progress === 'number'){
    stageProgress = Math.max(stageProgress, progress);
    modalProgress.style.width = `${stageProgress}%`;
    dom.taskProgress.style.width = `${stageProgress}%`;
  }
}

function resetRuntimeState(){
  evidenceCount = 0;
  latestFinalReport = '';
  currentWorkflowStage = 'planner';
  workflowStageStates = Object.fromEntries(workflowStages.map(s=>[s,'waiting']));
  stageProgress = 0;
  resetAgentStates();
  modalSteps.forEach(el=>el.classList.remove('active','done','replan','failed'));
  if(modalCard) modalCard.classList.remove('critic-current');
  dom.coverage.textContent = '等待任务';
  dom.green.textContent = '暂无证据';
  dom.shadow.textContent = '未生成';
  dom.healthScore.textContent = '—';
  dom.statusGlyphLabel.innerHTML = 'ANALYSIS<br>STATUS';
  dom.healthRing.style.setProperty('--score','0');
  dom.reportOverview.textContent = '等待生成分析报告。';
  dom.reportStatus.textContent = '等待生成';
  dom.paperStatus.textContent = '等待生成';
  if(dom.exportReport) dom.exportReport.hidden = true;
  setAnalysisStatus('waiting','等待分析','上传林草场景图片并提交分析需求后，系统将在此展示执行状态。');
  clearAgentTrace();
}

function renderScene(index, {keepCustom=false} = {}) {
  currentScene = index;
  const s = scenes[index];
  if (!keepCustom) {
    customImage = null;
    dom.mainImage.src = `assets/scene-0${s.id}.png`;
  }
  dom.sceneLabel.textContent = customImage ? `CUSTOM INPUT · ${customImage.name}` : s.label;
  dom.hud.textContent = customImage ? 'CUSTOM IMAGE · MULTI-AGENT ANALYSIS' : s.hud;
  dom.taskObservation.textContent = customImage ? `已载入“${customImage.name}”，等待开始真实分析。` : '上传林草场景图片后，系统将在此展示智能分析结果。';
  dom.coverage.textContent = '等待任务';
  dom.green.textContent = '暂无证据';
  dom.shadow.textContent = '未生成';
  dom.vegetationText.textContent = '上传图片并开始分析后，完整研判结果将在下方报告中展示。';
  dom.overallRisk.textContent = '等待分析';
  dom.primaryRisk.textContent = '暂无分析结果';
  dom.riskIntro.textContent = '系统完成分析后将提供风险研判，请以最终报告为准。';
  dom.riskList.innerHTML = '<p class="insight-empty">暂无分析结果</p>';
  dom.actionList.innerHTML = '<p class="insight-empty">报告生成后显示治理建议</p>';
  dom.reportSceneName.textContent = customImage ? `自定义影像：${customImage.name}` : s.title;
  dom.reportNo.textContent = 'AI ANALYSIS REPORT';
  dom.paperCode.textContent = '—';
  dom.paperSceneTitle.textContent = customImage ? '自定义影像分析场景' : s.shortTitle;
  dom.reportOverview.textContent = '等待生成分析报告。';
  dom.reportStatus.textContent = '等待生成';
  dom.paperStatus.textContent = '等待生成';
  if (dom.exportReport) dom.exportReport.hidden = true;
  evidenceCount = 0;
  latestFinalReport = '';
  dom.currentFileName.textContent = customImage ? customImage.name : '示例影像已选择';
  resetAgentStates();
  setAnalysisStatus('waiting','等待分析','上传林草场景图片并提交分析需求后，系统将在此展示执行状态。');
  clearAgentTrace();
  $$('.scene-card').forEach((c,i)=>c.classList.toggle('active', i===index && !customImage));
}

renderScene(0);

// Scroll reveal + nav state
const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in'); });
}, {threshold:.12});
$$('.reveal').forEach(el=>revealObserver.observe(el));

const sections = $$('main section[id]');
const navLinks = $$('.site-nav a');
const sectionObserver = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if(e.isIntersecting){ navLinks.forEach(a=>a.classList.toggle('active', a.getAttribute('href')===`#${e.target.id}`)); }
  });
},{rootMargin:'-35% 0px -55% 0px'});
sections.forEach(s=>sectionObserver.observe(s));

window.addEventListener('scroll',()=>{
  const max = document.documentElement.scrollHeight - innerHeight;
  const ratio = max > 0 ? scrollY/max : 0;
  dom.progress.style.width = `${ratio*100}%`;
  dom.header.classList.toggle('scrolled', scrollY>24);
});

// Counter animation
const metricObserver = new IntersectionObserver(entries=>entries.forEach(e=>{
  if(!e.isIntersecting || e.target.dataset.counted) return;
  e.target.dataset.counted='1';
  const end = +e.target.dataset.count;
  let n=0; const step=()=>{ n++; e.target.textContent=n.toString().padStart(2,'0'); if(n<end) setTimeout(step,80); }; step();
}),{threshold:.7});
$$('[data-count]').forEach(el=>metricObserver.observe(el));

// Scene cards
$$('.scene-card').forEach(card=>card.addEventListener('click',()=>{
  const i=+card.dataset.scene;
  dom.mainImage.style.opacity=.35;
  setTimeout(()=>{ renderScene(i); dom.mainImage.style.opacity=1; },180);
  dom.analysisStateText.textContent='示例影像已切换 · 数据就绪';
}));

// Upload & drag drop
const fileInput = $('#imageUpload');
const dropZone = $('#dropZone');
function handleFile(file){
  if(!file || !file.type.startsWith('image/')) return;
  currentImageFile = file;
  const reader = new FileReader();
  reader.onload = e => {
    customImage={name:file.name};
    dom.mainImage.src=e.target.result;
    renderScene(0,{keepCustom:true});
    dom.currentFileName.textContent=file.name;
    setAnalysisStatus('waiting','等待分析','图片已载入，请补充分析需求并开始智能分析。');
    dom.taskProgress.style.width='18%';
    $$('.scene-card').forEach(c=>c.classList.remove('active'));
    showToast('图像上传成功，可开始协同分析');
  };
  reader.readAsDataURL(file);
}
fileInput.addEventListener('change',e=>handleFile(e.target.files[0]));
['dragenter','dragover'].forEach(ev=>dropZone.addEventListener(ev,e=>{e.preventDefault();dropZone.classList.add('dragover')}));
['dragleave','drop'].forEach(ev=>dropZone.addEventListener(ev,e=>{e.preventDefault();dropZone.classList.remove('dragover')}));
dropZone.addEventListener('drop',e=>handleFile(e.dataTransfer.files[0]));

$$('.prompt-presets button').forEach(button=>button.addEventListener('click',()=>{
  dom.analysisPrompt.value = button.dataset.prompt || '';
  dom.analysisPrompt.focus();
}));

// 真实多智能体分析：上传影像 → FastAPI → Agent graph → 返回报告
const API_BASE = 'http://127.0.0.1:8001';
const modal=$('#analysisModal'), modalCard=$('.modal-card'), modalSteps=$$('#modalSteps>div'), modalProgress=$('#modalProgress'), modalText=$('#modalText');

async function getCurrentImageFile(){
  if(currentImageFile) return currentImageFile;
  // 示例影像：把当前显示的图片抓取为 File 后再上传
  const src = dom.mainImage.src;
  const res = await fetch(src);
  const blob = await res.blob();
  const name = src.split('/').pop() || 'scene.png';
  return new File([blob], name, {type: blob.type || 'image/png'});
}

function closeAnalysisModal(){
  modal.classList.remove('open'); modal.setAttribute('aria-hidden','true');
  dom.scan.classList.remove('scanning');
  if(modalCard) modalCard.classList.remove('critic-current');
  modalSteps.forEach(s=>{s.classList.remove('active','done','replan','failed')});
  modalProgress.style.width='0%';
}

// ---------- SSE V1：真实 Agent Timeline ----------
function clearAgentTrace(){
  dom.agentTrace.innerHTML = '<p class="trace-empty">等待分析任务 · 真实 Agent 事件将在运行后显示</p>';
}

function appendTrace(label, text, final=false){
  const p = document.createElement('p');
  const time = document.createElement('span'); time.textContent = final ? 'DONE' : 'EVENT';
  const tag = document.createElement('b'); tag.textContent = `[${label}]`;
  p.append(time, tag, document.createTextNode(` ${text}`));
  if(final) p.className = 'trace-final';
  dom.agentTrace.appendChild(p);
}

function sanitizeReportForDisplay(text){
  return String(text || '')
    .replace(/[A-Za-z]:\\Users\\[^\s，。；：,.;)）]+\\AppData\\Local\\Temp\\[^\s，。；：,.;)）]+/gi, '上传图片')
    .replace(/\/(?:tmp|var\/tmp)\/[^\s，。；：,.;)）]+/gi, '上传图片');
}

function appendInlineMarkdown(text, parent){
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g);
  parts.forEach(part=>{
    if(/^\*\*[^*]+\*\*$/.test(part)){
      const strong = document.createElement('strong');
      strong.textContent = part.slice(2,-2); parent.appendChild(strong);
    }else if(part){ parent.appendChild(document.createTextNode(part)); }
  });
}

function splitTableRow(line){
  const value = String(line || '').trim().replace(/^\|/, '').replace(/\|$/, '');
  return value.split('|').map(cell=>cell.trim());
}

function isTableSeparator(line){
  const cells = splitTableRow(line);
  return cells.length >= 2 && cells.every(cell=>/^:?-{3,}:?$/.test(cell));
}

function isPipeRow(line){
  return String(line || '').includes('|') && splitTableRow(line).length >= 2;
}

function appendReportTable(headers, rows, root){
  const wrap = document.createElement('div');
  wrap.className = 'report-table-wrap';
  const table = document.createElement('table');
  table.className = 'report-table';
  const thead = document.createElement('thead');
  const headRow = document.createElement('tr');
  headers.forEach(cell=>{ const th=document.createElement('th'); appendInlineMarkdown(cell, th); headRow.appendChild(th); });
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = document.createElement('tbody');
  rows.forEach(row=>{
    const tr = document.createElement('tr');
    headers.forEach((_, index)=>{ const td=document.createElement('td'); appendInlineMarkdown(row[index] || '', td); tr.appendChild(td); });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
  root.appendChild(wrap);
}

function safeMarkdownLiteRender(reportText){
  const root = dom.reportOverview;
  root.replaceChildren();
  const lines = sanitizeReportForDisplay(reportText).replace(/\r\n?/g,'\n').split('\n');
  let i = 0;
  while(i < lines.length){
    const line = lines[i];
    if(!line.trim()){ i++; continue; }
    if(isPipeRow(line) && i + 1 < lines.length && isTableSeparator(lines[i + 1])){
      const headers = splitTableRow(line);
      i += 2;
      const rows = [];
      while(i < lines.length && lines[i].trim() && isPipeRow(lines[i])){
        rows.push(splitTableRow(lines[i]));
        i++;
      }
      appendReportTable(headers, rows, root);
      continue;
    }
    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if(heading){ const el=document.createElement(`h${heading[1].length}`); appendInlineMarkdown(heading[2].trim(),el); root.appendChild(el); i++; continue; }
    if(/^---+$/.test(line.trim())){ root.appendChild(document.createElement('hr')); i++; continue; }
    if(/^>\s?/.test(line)){
      const el=document.createElement('blockquote'); appendInlineMarkdown(line.replace(/^>\s?/,'').trim(),el); root.appendChild(el); i++; continue;
    }
    if(/^[-*]\s+/.test(line)){
      const list=document.createElement('ul');
      while(i<lines.length && /^[-*]\s+/.test(lines[i])){ const li=document.createElement('li'); appendInlineMarkdown(lines[i].replace(/^[-*]\s+/,'').trim(),li); list.appendChild(li); i++; }
      root.appendChild(list); continue;
    }
    if(/^\d+[.)]\s+/.test(line)){
      const list=document.createElement('ol');
      while(i<lines.length && /^\d+[.)]\s+/.test(lines[i])){ const li=document.createElement('li'); appendInlineMarkdown(lines[i].replace(/^\d+[.)]\s+/,'').trim(),li); list.appendChild(li); i++; }
      root.appendChild(list); continue;
    }
    const paragraph=[];
    while(i<lines.length && lines[i].trim() && !/^(#{1,3})\s+|^---+$|^>\s?|^[-*]\s+|^\d+[.)]\s+/.test(lines[i])) paragraph.push(lines[i++].trim());
    const p=document.createElement('p'); appendInlineMarkdown(paragraph.join(' '),p); root.appendChild(p);
  }
}

function setStage(text, proposed){
  stageProgress = Math.max(stageProgress, proposed);
  modalText.textContent = text;
  modalProgress.style.width = `${stageProgress}%`;
  dom.taskProgress.style.width = `${stageProgress}%`;
}

function parseSSEFrame(frame){
  const lines = frame.split('\n');
  let event = 'message';
  const dataLines = [];
  for(const line of lines){
    if(line.startsWith('event:')) event = line.slice(6).trim();
    else if(line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''));
  }
  if(!dataLines.length) return null;
  const dataStr = dataLines.join('\n');
  let data = {};
  try{ data = JSON.parse(dataStr); }catch(_){ data = {message: dataStr}; }
  return {event, data};
}

async function readSSEStream(response, onEvent){
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  while(true){
    const {done, value} = await reader.read();
    if(done) break;
    buffer += decoder.decode(value, {stream:true});
    buffer = buffer.replace(/\r\n/g, '\n');
    let idx;
    while((idx = buffer.indexOf('\n\n')) !== -1){
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const parsed = parseSSEFrame(frame);
      if(parsed) onEvent(parsed.event, parsed.data);
    }
  }
  // 冲刷 decoder 尾部 + 残余 frame
  buffer += decoder.decode();
  buffer = buffer.replace(/\r\n/g, '\n');
  if(buffer.trim()){
    const parsed = parseSSEFrame(buffer);
    if(parsed) onEvent(parsed.event, parsed.data);
  }
}

function handleSSEEvent(event, data){
  switch(event){
    case 'run_started':
      setStage('分析任务已启动', 5);
      dom.reportStatus.textContent = '分析中'; dom.paperStatus.textContent = '分析中';
      setAgentState('planner','active');
      setWorkflowStage('planner','active','任务规划',15);
      dom.coverage.textContent = '任务规划'; dom.green.textContent = '等待生成'; dom.shadow.textContent = '等待生成';
      dom.healthTitle.textContent = '正在分析'; dom.healthScore.textContent = '01'; dom.statusGlyphLabel.innerHTML = 'PLANNER<br>ACTIVE';
      setAnalysisStatus('active','正在执行多智能体协同分析','任务规划已启动，系统正在调度视觉与知识分析。');
      appendTrace('SYS', '分析任务已启动');
      break;
    case 'planner_completed': {
      const n = (data.steps && data.steps.length) || 0;
      setStage(`Planner 规划完成 · 第 ${data.plan_loop} 轮 · ${n} 个任务`, 15);
      setAgentState('planner','completed'); setAgentState('executor','active');
      setWorkflowStage('planner','completed','任务规划完成',15);
      dom.coverage.textContent = '任务规划完成';
      setAnalysisStatus('active','正在执行多智能体协同分析',`任务规划完成，已生成 ${n} 个待执行任务。`);
      appendTrace('PLANNER', `Round ${data.plan_loop} · 生成 ${n} 个任务`);
      break;
    }
    case 'executor_completed': {
      const name = data.task_name || data.task_id || '';
      setStage(`Executor 执行完成 · ${name}`, 35);
      setAgentState('executor','completed');
      dom.coverage.textContent = '多模态分析';
      appendTrace('EXECUTOR', `${data.task_id || ''}${name ? ' · ' + name : ''} 完成`);
      break;
    }
    case 'evidence_created': {
      const isVision = data.type === 'vision';
      const label = isVision ? 'VISION' : 'RAG';
      const desc = isVision ? '视觉证据' : (data.source || data.tool_name || '知识证据');
      setStage(`登记证据 ${data.evidence_id}`, 45);
      setAgentState(isVision ? 'vision' : 'knowledge','completed');
      setWorkflowStage(isVision ? 'vision' : 'knowledge','completed', isVision ? '多模态感知' : '知识检索', isVision ? 35 : 55);
      evidenceCount += 1;
      dom.green.textContent = `已登记 ${evidenceCount} 条证据`;
      dom.statusGlyphLabel.innerHTML = isVision ? 'VISION<br>DONE' : 'KNOWLEDGE<br>DONE';
      setAnalysisStatus('active','正在执行多智能体协同分析',`已登记新的${isVision ? '视觉' : '知识'}证据。`);
      appendTrace(label, `Evidence ${data.evidence_id} · ${desc}`);
      break;
    }
    case 'critic_result': {
      const status = data.status || (data.action === 'replan' ? 'replan' : 'finalize');
      if(status === 'replan'){
        setStage('Critic · 证据不足 · 触发重新规划', 55);
        setAgentState('critic','replan'); setAgentState('planner','active');
        setWorkflowStage('critic','replan','需要补充分析',60); dom.statusGlyphLabel.innerHTML = 'CRITIC<br>REPLAN';
        dom.coverage.textContent = '正在补充分析';
        setAnalysisStatus('replan','需要补充分析 / 重新规划','质量审查发现证据不足，系统将补充任务后再次分析。');
        appendTrace('CRITIC', '证据不足，触发重新规划');
      } else if(status === 'passed'){
        setStage('Critic · 审查通过 · 进入报告生成', 80);
        setAgentState('critic','completed'); setAnalysisStatus('active','正在执行多智能体协同分析','质量审查通过，正在生成最终报告。');
        setWorkflowStage('critic','completed','质量审查通过',75); dom.coverage.textContent = '质量审查通过'; dom.statusGlyphLabel.innerHTML = 'CRITIC<br>DONE';
        appendTrace('CRITIC', '审查通过');
      } else if(status === 'soft_landing'){
        setStage('Critic · 达到最大迭代次数 · 进入质量软着陆', 80);
        setAgentState('critic','completed'); setAnalysisStatus('active','正在执行多智能体协同分析','质量审查完成，正在生成降级报告。');
        setWorkflowStage('critic','completed','完成有限证据研判',75); dom.coverage.textContent = '完成有限证据研判'; dom.statusGlyphLabel.innerHTML = 'CRITIC<br>DONE';
        appendTrace('CRITIC', '达到最大迭代次数，进入质量软着陆');
      } else if(status === 'deadlock'){
        setStage('Critic · 检测到执行异常 · 进入降级处理', 80);
        setAgentState('critic','failed'); setAnalysisStatus('failed','分析未完成','执行流程未能继续，请稍后重新提交分析任务。');
        setWorkflowStage('critic','failed','分析中断',0); dom.coverage.textContent = '分析中断'; dom.healthScore.textContent = '!'; dom.statusGlyphLabel.innerHTML = 'ERROR';
        appendTrace('CRITIC', '检测到执行异常，进入降级处理');
      } else {
        setStage('Critic 审查完成 · 进入报告生成', 80);
        appendTrace('CRITIC', '审查完成，进入报告生成');
      }
      break;
    }
    case 'finalizer_completed':
      setStage('Finalizer 报告生成完成', 90);
      setAgentState('finalizer','completed');
      setWorkflowStage('finalizer','completed','报告生成',90); dom.coverage.textContent = '报告生成'; dom.statusGlyphLabel.innerHTML = 'FINALIZER<br>DONE';
      appendTrace('FINALIZER', '报告生成完成');
      break;
    case 'final_report':
      latestFinalReport = sanitizeReportForDisplay(data.report || '');
      safeMarkdownLiteRender(latestFinalReport);
      dom.reportStatus.textContent = '生成完成'; dom.paperStatus.textContent = '生成完成';
      dom.shadow.textContent = '已生成'; dom.healthScore.textContent = '✓'; dom.statusGlyphLabel.innerHTML = 'COMPLETE';
      setWorkflowStage('finalizer','completed','报告生成完成',95);
      if (dom.exportReport) dom.exportReport.hidden = false;
      dom.paperSceneTitle.textContent = '实时多智能体分析报告';
      dom.reportSceneName.textContent = customImage ? `实时分析：${customImage.name}` : '实时分析结果';
      break;
    case 'run_completed':
      sseRunFinished = true;
      if(data.success === true){
        closeAnalysisModal();
        dom.analysisStateText.textContent = '协同分析完成 · 结果已同步';
        dom.analysisStateDot.style.background = '#739353';
        dom.taskProgress.style.width = '100%';
        modalProgress.style.width = '100%';
        setAnalysisStatus('completed','分析已完成','完整结果已生成，请查看下方智能分析报告。');
        dom.coverage.textContent = '已完成'; dom.green.textContent = `已登记 ${evidenceCount} 条证据`; dom.shadow.textContent = '已生成';
        setWorkflowStage('finalizer','completed','分析完成',100); dom.statusGlyphLabel.innerHTML = 'COMPLETE';
        appendTrace('SYS', '分析完成', true);
        showToast('分析完成，真实报告已生成');
      } else {
        closeAnalysisModal();
        setAnalysisStatus('failed','分析未完成','请稍后重新提交分析任务。');
        dom.analysisStateDot.style.background = '#c0563c';
        dom.taskProgress.style.width = '0%';
        modalProgress.style.width = '0%';
        dom.reportStatus.textContent = '生成失败'; dom.paperStatus.textContent = '生成失败';
        dom.reportOverview.textContent = '分析未能完成，未生成最终报告。';
        dom.coverage.textContent = '分析中断'; dom.healthScore.textContent = '!'; dom.statusGlyphLabel.innerHTML = 'ERROR';
        setWorkflowStage(currentWorkflowStage,'failed','分析中断',0);
        if (dom.exportReport) dom.exportReport.hidden = true;
        appendTrace('SYS', '分析未完成');
        if(!sseErrorSeen) showToast('分析失败，请稍后重试');
      }
      break;
    case 'error':
      sseErrorSeen = true;
      closeAnalysisModal();
      setAnalysisStatus('failed','分析未完成','请稍后重新提交分析任务。');
      dom.analysisStateDot.style.background = '#c0563c';
      dom.taskProgress.style.width = '0%';
      setWorkflowStage(currentWorkflowStage,'failed','分析中断',0); dom.healthScore.textContent = '!'; dom.statusGlyphLabel.innerHTML = 'ERROR';
      dom.reportStatus.textContent = '生成失败'; dom.paperStatus.textContent = '生成失败';
      dom.reportOverview.textContent = '分析未能完成，未生成最终报告。';
      if (dom.exportReport) dom.exportReport.hidden = true;
      showToast('分析失败，请稍后重试');
      break;
  }
}

async function runAnalysis(){
  if(isAnalyzing) return;
  const file = await getCurrentImageFile();
  if(!file){ showToast('请先上传一张图片，或选择示例影像'); return; }

  isAnalyzing = true;
  dom.runButton.disabled = true;
  dom.runButton.querySelector('span').textContent = '正在分析…';
  resetRuntimeState();
  dom.reportOverview.textContent = '多智能体系统正在生成综合分析报告……';
  dom.reportStatus.textContent = '分析中'; dom.paperStatus.textContent = '分析中';

  // 复用现有 loading 视觉：打开分析 modal + 扫描线
  modal.classList.add('open'); modal.setAttribute('aria-hidden','false');
  dom.scan.classList.add('scanning'); dom.taskProgress.style.width='12%';
  setAnalysisStatus('active','正在执行多智能体协同分析','系统正在调度任务规划、视觉感知、知识检索与质量审查。'); dom.analysisStateDot.style.background='#d9a861';
  setWorkflowStage('planner','active','任务规划',15);
  modalProgress.style.width='10%';
  modalText.textContent='正在上传影像并调用多智能体系统...';
  stageProgress = 10;
  sseRunFinished = false;
  sseErrorSeen = false;
  clearAgentTrace();
  appendTrace('SYS', '建立 SSE 流式连接');

  const fd = new FormData();
  fd.append('image', file, file.name);
  fd.append('prompt', dom.analysisPrompt.value.trim());

  try{
    const res = await fetch(`${API_BASE}/api/analyze-stream`, { method:'POST', body: fd });
    if(!res.ok){
      let msg = `请求失败 (HTTP ${res.status})`;
      try{ const j = await res.json(); if(j && j.error) msg = j.error; }catch(_){}
      throw new Error(msg);
    }
    if(!res.body){ throw new Error('当前浏览器不支持流式响应读取'); }
    await readSSEStream(res, handleSSEEvent);
    if(!sseRunFinished){
      throw new Error('流式响应意外中断');
    }
  }catch(err){
    closeAnalysisModal();
    dom.analysisStateText.textContent='分析失败'; dom.analysisStateDot.style.background='#c0563c'; dom.taskProgress.style.width='0%';
    setAnalysisStatus('failed','分析未完成','请稍后重新提交分析任务。');
    dom.reportStatus.textContent = '生成失败'; dom.paperStatus.textContent = '生成失败';
    dom.reportOverview.textContent = '分析未能完成，未生成最终报告。';
    showToast('分析失败，请稍后重试');
  }finally{
    isAnalyzing = false;
    dom.runButton.disabled = false;
    dom.runButton.querySelector('span').textContent = '开始智能分析';
  }
}
$('#runAnalysis').addEventListener('click',runAnalysis);

// Export the current real final report
const paperLoading=$('#paperLoading');
$('#exportReport').addEventListener('click',()=>{
  const text = latestFinalReport.trim();
  if(!text || text === '等待生成分析报告。') return;
  const blob=new Blob([text],{type:'text/plain;charset=utf-8'});
  const url=URL.createObjectURL(blob); const a=document.createElement('a');
  a.href=url; a.download='青穹林草智能分析报告.txt'; a.click(); URL.revokeObjectURL(url);
  showToast('分析报告已导出');
});

// Toast
let toastTimer;
function showToast(text){const t=$('#toast');$('span',t).textContent=text;t.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),2600)}

// Menu
const menuToggle=$('#menuToggle'), nav=$('.site-nav');
menuToggle.addEventListener('click',()=>{nav.classList.toggle('open');document.body.classList.toggle('menu-open')});
navLinks.forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');document.body.classList.remove('menu-open')}));

// subtle tilt, disabled on touch
if(matchMedia('(hover:hover)').matches){
  $$('.tilt').forEach(el=>{
    el.addEventListener('mousemove',e=>{const r=el.getBoundingClientRect();const x=(e.clientX-r.left)/r.width-.5;const y=(e.clientY-r.top)/r.height-.5;el.style.transform=`perspective(900px) rotateX(${y*-2.2}deg) rotateY(${x*2.8}deg) translateY(-1px)`});
    el.addEventListener('mouseleave',()=>el.style.transform='');
  });
  $$('.magnetic').forEach(el=>{
    el.addEventListener('mousemove',e=>{const r=el.getBoundingClientRect();const x=e.clientX-r.left-r.width/2;const y=e.clientY-r.top-r.height/2;el.style.transform=`translate(${x*.05}px,${y*.08}px)`});
    el.addEventListener('mouseleave',()=>el.style.transform='');
  });
}
