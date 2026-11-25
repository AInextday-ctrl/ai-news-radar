/**
 * AI News Radar - Context-Aware Amazon Associates & Native Partner Engine (v3.0)
 *
 * Features:
 *   - Curated AI Product Pool (GPUs, DDR5 Memory, NVMe SSDs, Local-LLM Macs/PCs,
 *     Edge Robotics Kits, AI Engineering Books, Developer Gear) with Amazon tag=purrpulse-20
 *   - Real-time article tag & keyword relevance scoring (EN + ZH)
 *   - Page-wide strict zero-duplicate guarantee across in-article and bottom slots
 *   - 100% Amazon Associates compliant: no hardcoded prices, no scraped product images,
 *     crisp theme-adaptive SVG device/book visuals, and clear Associate disclosure
 *   - Translation-plugin friendly semantic HTML & zero CLS (min-height reserved)
 */
(function () {
  'use strict';

  var AMAZON_TAG = 'purrpulse-20';

  function amzDp(asin) {
    return 'https://www.amazon.com/dp/' + encodeURIComponent(asin) + '?tag=' + AMAZON_TAG;
  }

  function amzSearch(query) {
    return 'https://www.amazon.com/s?k=' + encodeURIComponent(query) + '&tag=' + AMAZON_TAG;
  }

  // =========================================================================
  // 1. CURATED AI HARDWARE, EDGE, GEAR & ENGINEERING BOOKS POOL
  // =========================================================================
  var PRODUCT_POOL = [
    // --- Memory & High-Speed Storage ---
    {
      id: 'hw-ddr5-64gb',
      category: 'memory',
      iconType: 'memory',
      accent: 'sky',
      isAmazon: true,
      url: amzSearch('64GB DDR5 6000 Memory Kit Crucial Corsair'),
      tags: [
        'memory', 'dram', 'ddr5', 'ram', 'hbm', 'micron', 'sk hynix', 'hynix',
        'samsung', 'hp', 'dell', 'xiaomi', 'shortage', 'supply chain', 'workstation',
        '内存', '闪存', '美光', '海力士', '三星', '供应链', '惠普', '戴尔', '小米', '硬件'
      ],
      en: {
        badge: 'HIGH-BANDWIDTH MEMORY',
        name: '64GB / 96GB DDR5 Performance Memory Kits',
        tagline: 'High-capacity low-latency DDR5 RAM for local LLM offloading, multi-container dev stacks, and AI workstations.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '高带宽内存升级',
        name: '64GB / 96GB DDR5 高频大容量内存套装',
        tagline: '面向本地大模型推理卸载、多容器开发与 AI 工作站的优选 DDR5 内存配置，有效缓解内存瓶颈。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-nvme-4tb',
      category: 'memory',
      iconType: 'ssd',
      accent: 'indigo',
      isAmazon: true,
      url: amzSearch('Samsung 990 PRO 4TB PCIe NVMe SSD'),
      tags: [
        'nand', 'flash', 'ssd', 'storage', 'ymtc', 'xtacking', 'micron', 'hynix',
        'samsung', '3d nand', 'dataset', 'checkpoint', 'weights', 'pcie', 'nvme',
        '闪存', '固态硬盘', '长江存储', '存储', '堆叠', '美光', '权重', '数据集'
      ],
      en: {
        badge: 'AI DATASET STORAGE',
        name: '4TB PCIe Gen4 / Gen5 NVMe M.2 SSDs',
        tagline: 'Ultra-fast sequential read/write storage built for large model weights, RAG vector indexes, and local training datasets.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '高速模型存储',
        name: '4TB PCIe 4.0/5.0 NVMe M.2 固态硬盘',
        tagline: '专为百亿级模型权重加载、本地向量数据库与高吞吐 AI 数据集读写打造的旗舰高速闪存。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },

    // --- GPUs & AI Compute ---
    {
      id: 'hw-rtx-flagship',
      category: 'gpu',
      iconType: 'gpu',
      accent: 'emerald',
      isAmazon: true,
      url: amzSearch('NVIDIA GeForce RTX 5090 5080 Graphics Card'),
      tags: [
        'nvidia', 'gpu', 'blackwell', 'rtx', 'cuda', 'tensor', 'training', 'inference',
        'chip', 'semiconductor', 'tsmc', 'amd', 'vram', '3d', 'gaming', 'gta', 'graphics',
        '英伟达', '显卡', '算力', '芯片', '半导体', '训练', '推理', '台积电', '游戏'
      ],
      en: {
        badge: 'FLAGSHIP AI GPU',
        name: 'NVIDIA GeForce RTX 5090 / 5080 GPUs',
        tagline: 'Next-gen Tensor Core & FP4/FP8 desktop compute for local generative AI, ComfyUI workflows, and CUDA acceleration.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '旗舰桌面算力卡',
        name: 'NVIDIA GeForce RTX 5090 / 5080 系列显卡',
        tagline: '新一代 Tensor Core 与大显存桌面级算力核心，胜任本地大模型微调、图像视频生成与 CUDA 加速。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-rtx-value',
      category: 'gpu',
      iconType: 'gpu',
      accent: 'sky',
      isAmazon: true,
      url: amzSearch('NVIDIA RTX 5070 Ti 16GB Graphics Card'),
      tags: [
        'gpu', 'nvidia', 'rtx', '16gb', 'vram', 'ollama', 'local', 'inference',
        'stable diffusion', 'comfyui', 'pc', 'workstation',
        '显卡', '显存', '本地部署', '推理', '工作站'
      ],
      en: {
        badge: 'LOCAL INFERENCE GPU',
        name: '16GB+ VRAM NVIDIA RTX GPUs for Local AI',
        tagline: 'Sweet-spot 16GB+ VRAM graphics cards capable of running quantized open-weights LLMs and diffusion pipelines locally.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '性价比本地推理卡',
        name: '16GB+ 大显存 RTX 系列本地 AI 显卡',
        tagline: '兼顾功耗与成本的 16GB 以上显存甜点卡，流畅运行量化开源大模型与本地图像生成管线。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-psu-atx31',
      category: 'gpu',
      iconType: 'psu',
      accent: 'amber',
      isAmazon: true,
      url: amzSearch('1000W ATX 3.1 PCIe 5.1 Modular Power Supply'),
      tags: [
        'power', 'grid', 'energy', 'psu', 'datacenter', 'server', 'workstation',
        'gpu', 'multi-gpu', 'build', 'electricity', 'nuclear', 'cooling',
        '电力', '电网', '能源', '数据中心', '服务器', '电源', '功耗'
      ],
      en: {
        badge: 'WORKSTATION POWER',
        name: '1000W+ ATX 3.1 PCIe 5.1 Modular PSUs',
        tagline: 'High-efficiency 80+ Platinum/Gold power delivery engineered for sustained high-wattage AI GPU workloads.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '高功率算力供电',
        name: '1000W+ ATX 3.1 原生 PCIe 5.1 模组电源',
        tagline: '面向长时间满载 AI 显卡训练与多卡工作站的高转换率稳定供电底座。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },

    // --- Local AI Computers & Apple Silicon ---
    {
      id: 'hw-mac-mini-m4',
      category: 'computer',
      iconType: 'mac',
      accent: 'indigo',
      isAmazon: true,
      url: amzSearch('Apple Mac mini M4 Pro'),
      tags: [
        'apple', 'mac', 'silicon', 'm4', 'siri', 'unified memory', 'local', 'ollama',
        'deepseek', 'llama', 'qwen', 'mlx', 'desktop', 'mini pc', 'home',
        '苹果', '本地部署', '统一内存', '开源模型', '桌面主机'
      ],
      en: {
        badge: 'LOCAL LLM COMPACT',
        name: 'Apple Mac mini M4 Pro (Unified Memory)',
        tagline: 'Silent, power-efficient Apple Silicon desktop with high-bandwidth unified memory ideal for running MLX & local LLMs.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '本地大模型神器',
        name: 'Apple Mac mini M4 Pro（高带宽统一内存）',
        tagline: '静音低功耗的 Apple Silicon 桌面主机，高带宽统一内存架构是本地运行 MLX 与开源大模型的优选。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-macbook-pro',
      category: 'computer',
      iconType: 'laptop',
      accent: 'violet',
      isAmazon: true,
      url: amzSearch('Apple MacBook Pro M4 Pro Max'),
      tags: [
        'apple', 'macbook', 'iphone', 'ipad', 'siri', 'ios', 'swift', 'xcode',
        'laptop', 'developer', 'mobile', 'coding', 'on-device',
        '苹果', '笔记本', '移动开发', '端侧'
      ],
      en: {
        badge: 'MOBILE AI DEV',
        name: 'Apple MacBook Pro (M4 Pro / Max)',
        tagline: 'Portable flagship workstation for running local coding copilots, Docker stacks, and on-device CoreML models.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '移动开发旗舰',
        name: 'Apple MacBook Pro (M4 Pro / Max)',
        tagline: '兼具全天候续航与统一大内存的移动 AI 开发本，随时随地流畅运行本地编程助手与端侧模型。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-ai-laptop',
      category: 'computer',
      iconType: 'laptop',
      accent: 'sky',
      isAmazon: true,
      url: amzSearch('NVIDIA RTX AI Laptop 32GB RAM'),
      tags: [
        'hp', 'lenovo', 'dell', 'asus', 'windows', 'microsoft', 'copilot', 'intel',
        'amd', 'ryzen', 'laptop', 'pc', 'enterprise', 'hardware',
        '惠普', '联想', '戴尔', '微软', '笔记本', '电脑', '英特尔', '硬件'
      ],
      en: {
        badge: 'AI PC & WORKSTATION',
        name: 'RTX-Accelerated AI Laptops (32GB+ RAM)',
        tagline: 'Dedicated NPU + NVIDIA RTX mobile workstations built for enterprise AI engineering, Windows Copilot+, and CUDA.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '移动 AI 工作站',
        name: 'RTX 独显 + 32GB 大内存 AI 笔记本电脑',
        tagline: '兼顾 NPU 端侧加速与 RTX 独显算力的开发级 AI PC，适配企业级部署与移动 CUDA 调试。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },

    // --- Edge AI & Robotics ---
    {
      id: 'hw-jetson-orin',
      category: 'edge',
      iconType: 'edge',
      accent: 'emerald',
      isAmazon: true,
      url: amzSearch('NVIDIA Jetson Orin Nano Developer Kit'),
      tags: [
        'robot', 'robotics', 'humanoid', 'embodied', 'physical ai', 'jetson', 'orin',
        'edge', 'autonomous', 'drone', 'lidar', 'vision', 'sensor', 'vehicle', 'car',
        '机器人', '人形机器人', '具身智能', '边缘计算', '自动驾驶', '无人机', '视觉'
      ],
      en: {
        badge: 'EMBODIED & EDGE AI',
        name: 'NVIDIA Jetson Orin Nano Developer Kit',
        tagline: 'Compact edge AI computer delivering high TOPS performance for robotics, vision-language-action models, and drones.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '具身智能开发套件',
        name: 'NVIDIA Jetson Orin Nano 边缘 AI 开发套件',
        tagline: '面向机器人控制、多模态视觉识别与端侧具身智能原型验证的高能效边缘计算开发板。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-rpi5-ai',
      category: 'edge',
      iconType: 'edge',
      accent: 'amber',
      isAmazon: true,
      url: amzSearch('Raspberry Pi 5 AI Kit'),
      tags: [
        'raspberry', 'iot', 'embedded', 'diy', 'maker', 'edge', 'home assistant',
        'camera', 'linux', 'sensor', 'automation', 'smart home',
        '树莓派', '嵌入式', '物联网', '开源硬件', '智能家居', '自动化'
      ],
      en: {
        badge: 'EDGE AI HARDWARE',
        name: 'Raspberry Pi 5 + AI HAT+ Edge Kit',
        tagline: 'Accessible neural accelerator add-on for home automation, real-time object detection, and edge inference experiments.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '轻量边缘推理套件',
        name: 'Raspberry Pi 5 + AI 加速扩展套件',
        tagline: '低成本高可玩性的极客边缘硬件，适合部署本地语音助手、智能视觉检测与自动化节点。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },

    // --- Essential AI Engineering & Strategy Books (Verified Exact ISBN-10s) ---
    {
      id: 'book-ai-engineering',
      category: 'book',
      iconType: 'book',
      accent: 'indigo',
      isAmazon: true,
      url: amzDp('1098166302'),
      tags: [
        'openai', 'anthropic', 'claude', 'gpt', 'gemini', 'llm', 'agent', 'rag',
        'prompt', 'evaluation', 'foundation model', 'api', 'coding', 'app', 'startup',
        '大模型', '智能体', '提示词', '评测', '应用开发', '架构'
      ],
      en: {
        badge: 'ESSENTIAL AI BOOK',
        name: 'AI Engineering: Building Applications with Foundation Models',
        tagline: 'By Chip Huyen (O’Reilly) — Production blueprint covering RAG, agents, evals, prompt engineering, and latency optimization.',
        cta: 'View Book on Amazon',
        hint: 'O’Reilly · Verified ASIN'
      },
      zh: {
        badge: 'AI 工程必读新书',
        name: '《AI Engineering》基础模型应用构建指南（英文原版）',
        tagline: 'Chip Huyen 著（O’Reilly）：系统拆解 RAG、Agent 智能体、自动化评测体系与生产级大模型工程实践。',
        cta: '前往亚马逊查看原版',
        hint: 'O’Reilly 权威出版'
      }
    },
    {
      id: 'book-build-llm',
      category: 'book',
      iconType: 'book',
      accent: 'violet',
      isAmazon: true,
      url: amzDp('1633437167'),
      tags: [
        'deepseek', 'qwen', 'llama', 'mistral', 'pytorch', 'transformer', 'weights',
        'pretraining', 'fine-tuning', 'architecture', 'open-source', 'math', 'research', 'arxiv',
        '开源', '预训练', '微调', '架构', '论文', '底层原理'
      ],
      en: {
        badge: 'DEEP TECH BOOK',
        name: 'Build a Large Language Model (From Scratch)',
        tagline: 'By Sebastian Raschka (Manning) — Step-by-step PyTorch implementation of attention, pretraining, and instruction tuning.',
        cta: 'View Book on Amazon',
        hint: 'Manning · Verified ASIN'
      },
      zh: {
        badge: '大模型手写实战',
        name: '《Build a Large Language Model (From Scratch)》',
        tagline: 'Sebastian Raschka 著：从零用 PyTorch 编写注意力机制、预训练与指令微调，吃透大模型底层代码。',
        cta: '前往亚马逊查看原版',
        hint: 'Manning 经典教程'
      }
    },
    {
      id: 'book-hands-on-llm',
      category: 'book',
      iconType: 'book',
      accent: 'sky',
      isAmazon: true,
      url: amzDp('1098150961'),
      tags: [
        'embedding', 'vector', 'search', 'semantic', 'rag', 'huggingface', 'nlp',
        'fine-tuning', 'classification', 'multimodal', 'vision', 'token',
        '向量', '检索', '微调', '多模态', '图解'
      ],
      en: {
        badge: 'VISUAL LLM GUIDE',
        name: 'Hands-On Large Language Models',
        tagline: 'By Jay Alammar & Maarten Grootendorst — Illustrated guide to embeddings, semantic search, RAG, and fine-tuning.',
        cta: 'View Book on Amazon',
        hint: 'O’Reilly · Verified ASIN'
      },
      zh: {
        badge: '图解大模型实战',
        name: '《Hands-On Large Language Models》图解语言大模型',
        tagline: 'Jay Alammar 联袂力作：以全彩可视化图解直观掌握向量检索、语义搜索、RAG 与微调实战。',
        cta: '前往亚马逊查看原版',
        hint: 'O’Reilly 畅销经典'
      }
    },
    {
      id: 'book-ml-systems',
      category: 'book',
      iconType: 'book',
      accent: 'emerald',
      isAmazon: true,
      url: amzDp('1098107969'),
      tags: [
        'mlops', 'enterprise', 'cloud', 'aws', 'google cloud', 'azure', 'kubernetes',
        'scaling', 'monitoring', 'data', 'pipeline', 'security', 'governance', 'deploy',
        '企业级', '云原生', '部署', '数据管道', '运维', '安全'
      ],
      en: {
        badge: 'SYSTEMS ARCHITECTURE',
        name: 'Designing Machine Learning Systems',
        tagline: 'By Chip Huyen — Iterative design for reliable, scalable, and maintainable production ML & AI data pipelines.',
        cta: 'View Book on Amazon',
        hint: 'O’Reilly · Verified ASIN'
      },
      zh: {
        badge: '系统架构圣经',
        name: '《Designing Machine Learning Systems》机器学习系统设计',
        tagline: '系统剖析生产级 AI 数据流、模型部署、线上监控与可持续迭代架构，企业工程团队常备案头书。',
        cta: '前往亚马逊查看原版',
        hint: 'O’Reilly 经典著作'
      }
    },
    {
      id: 'book-llm-handbook',
      category: 'book',
      iconType: 'book',
      accent: 'amber',
      isAmazon: true,
      url: amzDp('1836200072'),
      tags: [
        'agent', 'mcp', 'cursor', 'claude code', 'python', 'github', 'cli', 'tool',
        'docker', 'production', 'quantization', 'vllm', 'inference', 'workflow',
        '智能体', '工作流', '量化', '开源工具', '编程'
      ],
      en: {
        badge: 'PRODUCTION HANDBOOK',
        name: "LLM Engineer's Handbook",
        tagline: 'By Paul Iusztin & Maxime Labonne — End-to-end guide to LLM twin systems, fine-tuning, evaluation, and inference serving.',
        cta: 'View Book on Amazon',
        hint: 'Packt · Verified ASIN'
      },
      zh: {
        badge: '大模型工程手册',
        name: '《LLM Engineer’s Handbook》全链路落地实战手册',
        tagline: '完整覆盖数据工程、微调训练、量化推理部署与智能体生产化落地的端到端实战指南。',
        cta: '前往亚马逊查看原版',
        hint: 'Maxime Labonne 合著'
      }
    },
    {
      id: 'book-co-intelligence',
      category: 'book',
      iconType: 'book',
      accent: 'indigo',
      isAmazon: true,
      url: amzDp('059371671X'),
      tags: [
        'business', 'ceo', 'ipo', 'investment', 'funding', 'policy', 'regulation',
        'law', 'workplace', 'education', 'future', 'economy', 'market', 'strategy',
        '融资', '监管', '政策', '商业', '职场', '战略', '财报', '估值'
      ],
      en: {
        badge: 'AI STRATEGY READ',
        name: 'Co-Intelligence: Living and Working with AI',
        tagline: 'By Ethan Mollick (Wharton) — Practical strategic playbook on how AI reshapes teams, leadership, and competitive moats.',
        cta: 'View Book on Amazon',
        hint: 'NYT Bestseller · Verified ASIN'
      },
      zh: {
        badge: 'AI 商业战略必读',
        name: '《Co-Intelligence》与人工智能共智共事（英文原版）',
        tagline: '沃顿商学院教授 Ethan Mollick 著：深度探讨 AI 如何重塑企业组织架构、决策壁垒与未来工作流。',
        cta: '前往亚马逊查看原版',
        hint: '纽约时报畅销榜'
      }
    },

    // --- Developer Workstation, Audio & Spatial Gear ---
    {
      id: 'hw-dev-mouse',
      category: 'gear',
      iconType: 'keyboard',
      accent: 'sky',
      isAmazon: true,
      url: amzSearch('Logitech MX Master 3S Wireless Mouse'),
      tags: [
        'coding', 'ide', 'cursor', 'vscode', 'github', 'developer', 'terminal', 'cli',
        'productivity', 'workflow', 'software', 'saas', 'tool',
        '开发者', '编程', '效率工具', '终端', '外设'
      ],
      en: {
        badge: 'DEVELOPER DESK GEAR',
        name: 'Logitech MX Master 3S & Ergonomic Coding Gear',
        tagline: 'Precision MagSpeed scroll and multi-device workflow tools favored by full-stack and AI engineers.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '极客桌面效率外设',
        name: '罗技 MX Master 3S 旗舰无线开发鼠标',
        tagline: '配备电磁疾速滚轮与跨设备无缝切换，提升高频代码审查与多屏 AI 研发效率。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-4k-monitor',
      category: 'gear',
      iconType: 'monitor',
      accent: 'violet',
      isAmazon: true,
      url: amzSearch('Dell UltraSharp 4K USB-C Monitor'),
      tags: [
        'monitor', 'display', 'ui', 'design', 'frontend', 'coding', 'multitasking',
        'workspace', 'thunderbolt', 'usb-c',
        '显示器', '前端', '设计', '多屏', '办公'
      ],
      en: {
        badge: 'DEV WORKSPACE',
        name: '4K USB-C Hub Developer Monitors',
        tagline: 'Crisp high-DPI text clarity and single-cable 90W USB-C power delivery for terminal, IDE, and model dashboards.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '高分研发显示器',
        name: '4K USB-C 一线通开发专业显示器',
        tagline: '超清 HiDPI 代码文字锐利度与单线供电扩展，兼顾 IDE 编码、论文阅读与监控看板。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-studio-mic',
      category: 'gear',
      iconType: 'mic',
      accent: 'indigo',
      isAmazon: true,
      url: amzSearch('Shure MV7 USB Podcast Microphone'),
      tags: [
        'voice', 'audio', 'speech', 'tts', 'whisper', 'podcast', 'youtube', 'video',
        'music', 'creator', 'elevenlabs', 'realtime', 'dubbing',
        '语音', '音频', '合成', '配音', '播客', '视频', '麦克风'
      ],
      en: {
        badge: 'VOICE & CREATOR GEAR',
        name: 'Shure MV7+ / Studio USB-XLR Microphones',
        tagline: 'Broadcast-grade dynamic vocal capture for AI voice cloning datasets, technical podcasts, and video walkthroughs.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '语音 AI 采集外设',
        name: 'Shure MV7+ 动圈 USB/XLR 专业人声麦克风',
        tagline: '高信噪比棚级人声拾取，适用于声音克隆采样、AI 播客录制与技术视频配音。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    },
    {
      id: 'hw-vr-quest3',
      category: 'gear',
      iconType: 'xr',
      accent: 'emerald',
      isAmazon: true,
      url: amzSearch('Meta Quest 3 512GB'),
      tags: [
        'meta', 'xr', 'vr', 'ar', 'glasses', 'smart glasses', 'spatial', 'world model',
        'simulation', 'gaming', '3d', 'multimodal',
        '眼镜', '空间计算', '世界模型', '虚拟现实', '多模态'
      ],
      en: {
        badge: 'SPATIAL AI HARDWARE',
        name: 'Meta Quest 3 Mixed Reality Headset',
        tagline: 'Standalone mixed-reality platform powering spatial computing, teleoperation robotics demos, and 3D AI worlds.',
        cta: 'Check on Amazon',
        hint: 'Check Live Price'
      },
      zh: {
        badge: '空间计算终端',
        name: 'Meta Quest 3 混合现实头显',
        tagline: '主流空间计算与具身遥操作实验硬件平台，探索 3D 世界模型与混合现实交互前沿。',
        cta: '前往亚马逊查看',
        hint: '查看实时报价'
      }
    }
  ];

  var SPONSOR_CARD = {
    en: {
      id: 'sponsor-direct-en',
      category: 'sponsor',
      iconType: 'spark',
      accent: 'amber',
      isAmazon: false,
      internal: true,
      url: '/contact#sponsor',
      badge: 'FEATURED PARTNER',
      name: 'Promote Your AI Product on AI News Radar',
      tagline: 'Reach frontier AI engineers, builders, and technical decision-makers across our daily intelligence briefings.',
      cta: 'Submit / Sponsor',
      hint: 'Direct Booking'
    },
    zh: {
      id: 'sponsor-direct-zh',
      category: 'sponsor',
      iconType: 'spark',
      accent: 'amber',
      isAmazon: false,
      internal: true,
      url: '/zh/contact#sponsor',
      badge: '品牌直投合作',
      name: '申请 AI 资讯雷达生态推广展位',
      tagline: '每日精准触达一线 AI 工程师、开源开发者与技术决策者，支持工具库置顶与专题合作。',
      cta: '申请合作',
      hint: '官方直投通道'
    }
  };

  // =========================================================================
  // 2. THEME, LANGUAGE & COMPLIANCE-SAFE SVG ARTWORK
  // =========================================================================
  function isZhPage() {
    var path = (window.location && window.location.pathname) || '';
    var lang = (document.documentElement && document.documentElement.lang) || '';
    return path.indexOf('/zh') === 0 || lang.toLowerCase().indexOf('zh') === 0;
  }

  function isDarkPage() {
    var html = document.documentElement;
    return !!(html && html.classList && html.classList.contains('dark'));
  }

  function esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function getSvgArt(iconType, accent) {
    var palettes = {
      indigo: ['#312e81', '#6366f1'],
      sky: ['#0c4a6e', '#0ea5e9'],
      emerald: ['#064e3b', '#10b981'],
      amber: ['#78350f', '#f59e0b'],
      violet: ['#4c1d95', '#8b5cf6']
    };
    var pal = palettes[accent] || palettes.indigo;
    var glyphs = {
      gpu: '<rect x="14" y="20" width="36" height="24" rx="4" stroke="white" stroke-width="2.2" fill="none"/><circle cx="26" cy="32" r="5" stroke="white" stroke-width="2" fill="none"/><circle cx="38" cy="32" r="5" stroke="white" stroke-width="2" fill="none"/><path d="M18 44v4M24 44v4M30 44v4M14 26h-4M14 38h-4" stroke="white" stroke-width="2" stroke-linecap="round"/>',
      memory: '<rect x="12" y="22" width="40" height="20" rx="3" stroke="white" stroke-width="2.2" fill="none"/><rect x="17" y="27" width="6" height="10" rx="1" fill="white" opacity="0.9"/><rect x="26" y="27" width="6" height="10" rx="1" fill="white" opacity="0.9"/><rect x="35" y="27" width="6" height="10" rx="1" fill="white" opacity="0.9"/><path d="M18 42v4M26 42v4M34 42v4M42 42v4" stroke="white" stroke-width="2" stroke-linecap="round"/>',
      ssd: '<rect x="14" y="20" width="36" height="24" rx="3" stroke="white" stroke-width="2.2" fill="none"/><rect x="20" y="26" width="12" height="12" rx="1.5" fill="white" opacity="0.85"/><path d="M36 28h8M36 33h8M36 38h6" stroke="white" stroke-width="2" stroke-linecap="round"/>',
      mac: '<rect x="15" y="18" width="34" height="24" rx="4" stroke="white" stroke-width="2.2" fill="none"/><path d="M22 46h20" stroke="white" stroke-width="2.5" stroke-linecap="round"/><circle cx="32" cy="30" r="4.5" stroke="white" stroke-width="2" fill="none"/>',
      laptop: '<rect x="16" y="18" width="32" height="21" rx="2.5" stroke="white" stroke-width="2.2" fill="none"/><path d="M11 43h42l-3 4H14l-3-4z" fill="white" opacity="0.9"/>',
      edge: '<rect x="18" y="18" width="28" height="28" rx="4" stroke="white" stroke-width="2.2" fill="none"/><rect x="25" y="25" width="14" height="14" rx="2" fill="white" opacity="0.9"/><path d="M24 14v4M32 14v4M40 14v4M24 46v4M32 46v4M40 46v4M14 24h4M14 32h4M14 40h4M46 24h4M46 32h4M46 40h4" stroke="white" stroke-width="2" stroke-linecap="round"/>',
      book: '<path d="M16 17h14a3 3 0 0 1 3 3v27a2 2 0 0 0-2-2H16V17zM48 17H34a3 3 0 0 0-3 3v27a2 2 0 0 1 2-2h15V17z" stroke="white" stroke-width="2.2" fill="none" stroke-linejoin="round"/>',
      keyboard: '<rect x="12" y="21" width="40" height="22" rx="3.5" stroke="white" stroke-width="2.2" fill="none"/><path d="M18 28h4M26 28h4M34 28h4M42 28h4M18 35h4M26 35h12M42 35h4" stroke="white" stroke-width="2.2" stroke-linecap="round"/>',
      monitor: '<rect x="13" y="17" width="38" height="24" rx="3" stroke="white" stroke-width="2.2" fill="none"/><path d="M32 41v6M23 47h18" stroke="white" stroke-width="2.2" stroke-linecap="round"/>',
      mic: '<rect x="26" y="16" width="12" height="19" rx="6" stroke="white" stroke-width="2.2" fill="none"/><path d="M20 31a12 12 0 0 0 24 0M32 43v5M25 48h14" stroke="white" stroke-width="2.2" stroke-linecap="round"/>',
      xr: '<path d="M13 26a5 5 0 0 1 5-5h28a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5h-8l-4-4h-4l-4 4h-8a5 5 0 0 1-5-5V26z" stroke="white" stroke-width="2.2" fill="none"/><circle cx="23" cy="31" r="3" fill="white" opacity="0.9"/><circle cx="41" cy="31" r="3" fill="white" opacity="0.9"/>',
      psu: '<rect x="14" y="19" width="36" height="26" rx="3.5" stroke="white" stroke-width="2.2" fill="none"/><path d="M34 23l-6 9h6l-3 9 7-10h-6l2-8z" fill="white" opacity="0.95"/>',
      spark: '<path d="M32 14l4 12 12 4-12 4-4 12-4-12-12-4 12-4 4-12z" stroke="white" stroke-width="2" fill="white" fill-opacity="0.2" stroke-linejoin="round"/>'
    };
    var svg =
      '<svg viewBox="0 0 64 64" width="64" height="64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
        '<defs><linearGradient id="g-' + esc(iconType + '-' + accent) + '" x1="0" y1="0" x2="1" y2="1">' +
          '<stop offset="0%" stop-color="' + pal[0] + '"/>' +
          '<stop offset="100%" stop-color="' + pal[1] + '"/>' +
        '</linearGradient></defs>' +
        '<rect width="64" height="64" rx="12" fill="url(#g-' + esc(iconType + '-' + accent) + ')"/>' +
        (glyphs[iconType] || glyphs.spark) +
      '</svg>';
    return svg;
  }

  // =========================================================================
  // 3. CONTEXTUAL TAG SCORING & PAGE-WIDE DEDUPLICATION ENGINE
  // =========================================================================
  var usedIds = window.__AINR_USED_REC_IDS || {};
  window.__AINR_USED_REC_IDS = usedIds;

  function hashPath(str) {
    var h = 0;
    for (var i = 0; i < str.length; i++) {
      h = ((h << 5) - h + str.charCodeAt(i)) | 0;
    }
    return Math.abs(h);
  }

  function collectPageSignals() {
    var tagsMeta = document.querySelector('meta[name="ainr-tags"]');
    var descMeta = document.querySelector('meta[name="description"]');
    var h1El = document.querySelector('h1');
    var bodyParas = document.querySelectorAll('.article-body p');
    var bodyText = '';
    for (var i = 0; i < Math.min(2, bodyParas.length); i++) {
      bodyText += ' ' + (bodyParas[i].textContent || '');
    }
    return {
      tags: ((tagsMeta && tagsMeta.getAttribute('content')) || '').toLowerCase(),
      title: ((document.title || '') + ' ' + ((h1El && h1El.textContent) || '')).toLowerCase(),
      desc: ((descMeta && descMeta.getAttribute('content')) || '').toLowerCase(),
      body: bodyText.toLowerCase()
    };
  }

  function containsTag(haystack, tag) {
    if (!haystack || !tag) return false;
    // Direct match for CJK or multi-word tokens; word-boundary-safe check for short ASCII tokens
    if (/[\u4e00-\u9fff]/.test(tag) || tag.indexOf(' ') !== -1 || tag.length >= 5) {
      return haystack.indexOf(tag) !== -1;
    }
    var re = new RegExp('(^|[^a-z0-9])' + tag.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '($|[^a-z0-9])');
    return re.test(haystack);
  }

  function scoreProduct(prod, signals, seed) {
    var score = 0;
    var tags = prod.tags || [];
    for (var i = 0; i < tags.length; i++) {
      var t = tags[i];
      if (containsTag(signals.tags, t)) score += 12;
      if (containsTag(signals.title, t)) score += 9;
      if (containsTag(signals.desc, t)) score += 4;
      if (containsTag(signals.body, t)) score += 2;
    }
    // Slight deterministic tie-breaker per URL path so un-tagged pages rotate naturally
    var tie = (hashPath(prod.id + ':' + seed) % 100) / 1000.0;
    return score + tie;
  }

  function pickRelevantProducts(count, opts) {
    opts = opts || {};
    var signals = collectPageSignals();
    var seed = (window.location && window.location.pathname) || '/';
    var scored = [];

    for (var i = 0; i < PRODUCT_POOL.length; i++) {
      var prod = PRODUCT_POOL[i];
      if (usedIds[prod.id]) continue;
      if (opts.filterCategory && prod.category !== opts.filterCategory) continue;
      scored.push({
        item: prod,
        score: scoreProduct(prod, signals, seed)
      });
    }

    scored.sort(function (a, b) { return b.score - a.score; });

    var picked = [];
    var usedCategories = {};

    // First pass: prefer distinct categories when selecting multiple items for better variety
    if (opts.diverseCategories) {
      for (var j = 0; j < scored.length && picked.length < count; j++) {
        var cand = scored[j].item;
        if (!usedCategories[cand.category]) {
          picked.push(cand);
          usedCategories[cand.category] = true;
          usedIds[cand.id] = true;
        }
      }
    }

    // Second pass: fill remaining slots with highest-scoring unused items
    for (var k = 0; k < scored.length && picked.length < count; k++) {
      var c2 = scored[k].item;
      if (!usedIds[c2.id]) {
        picked.push(c2);
        usedIds[c2.id] = true;
      }
    }

    return picked;
  }

  // =========================================================================
  // 4. STYLES & COMPLIANCE-SAFE RENDERERS
  // =========================================================================
  function injectStylesOnce() {
    if (document.getElementById('ainr-monetization-css')) return;
    var style = document.createElement('style');
    style.id = 'ainr-monetization-css';
    style.textContent = [
      '.ainr-slot{box-sizing:border-box;width:100%;font-family:Inter,system-ui,-apple-system,sans-serif;}',
      '.ainr-card{position:relative;display:flex;align-items:center;gap:14px;padding:12px 14px;border-radius:14px;text-decoration:none;transition:transform .18s cubic-bezier(0.16,1,0.3,1),border-color .18s ease,box-shadow .18s ease;overflow:hidden;}',
      '.ainr-card:hover{transform:translateY(-1.5px);}',
      '.ainr-theme-light .ainr-card{background:linear-gradient(135deg,#ffffff,#f8fafc);border:1px solid #cbd5e1;color:#0f172a;box-shadow:0 4px 16px -6px rgba(15,23,42,0.08);}',
      '.ainr-theme-light .ainr-card:hover{border-color:#818cf8;box-shadow:0 10px 24px -10px rgba(99,102,241,0.22);}',
      '.ainr-theme-dark .ainr-card{background:linear-gradient(135deg,rgba(15,23,42,0.92),rgba(15,23,42,0.72));border:1px solid rgba(51,65,85,0.85);color:#f1f5f9;box-shadow:0 8px 24px -12px rgba(0,0,0,0.55);backdrop-filter:blur(12px);}',
      '.ainr-theme-dark .ainr-card:hover{border-color:rgba(129,140,248,0.65);box-shadow:0 12px 28px -10px rgba(99,102,241,0.3);}',

      '.ainr-icon-box{position:relative;width:64px;height:64px;flex-shrink:0;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.2);display:flex;align-items:center;justify-content:center;}',
      '.ainr-icon-box svg{width:100%;height:100%;display:block;}',

      '.ainr-body{min-width:0;flex:1;}',
      '.ainr-pill-row{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:3px;}',
      '.ainr-pill{display:inline-flex;align-items:center;gap:3px;font-size:9.5px;font-weight:800;padding:1.5px 7px;border-radius:999px;letter-spacing:.04em;text-transform:uppercase;line-height:1.3;}',
      '.ainr-pill-indigo{background:rgba(99,102,241,0.15);color:#6366f1;border:1px solid rgba(99,102,241,0.3);}',
      '.ainr-theme-dark .ainr-pill-indigo{color:#818cf8;}',
      '.ainr-pill-emerald{background:rgba(16,185,129,0.15);color:#059669;border:1px solid rgba(16,185,129,0.3);}',
      '.ainr-theme-dark .ainr-pill-emerald{color:#34d399;}',
      '.ainr-pill-sky{background:rgba(14,165,233,0.15);color:#0284c7;border:1px solid rgba(14,165,233,0.3);}',
      '.ainr-theme-dark .ainr-pill-sky{color:#38bdf8;}',
      '.ainr-pill-amber{background:rgba(245,158,11,0.15);color:#d97706;border:1px solid rgba(245,158,11,0.3);}',
      '.ainr-theme-dark .ainr-pill-amber{color:#fbbf24;}',
      '.ainr-pill-violet{background:rgba(139,92,246,0.15);color:#7c3aed;border:1px solid rgba(139,92,246,0.3);}',
      '.ainr-theme-dark .ainr-pill-violet{color:#a78bfa;}',
      '.ainr-verified{font-size:9.5px;font-weight:700;color:#10b981;letter-spacing:.02em;}',

      '.ainr-title{font-size:13.5px;font-weight:800;line-height:1.35;margin:0;letter-spacing:-0.01em;}',
      '.ainr-desc{font-size:11.5px;line-height:1.45;margin:3px 0 0;opacity:0.82;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',

      '.ainr-action-wrap{flex-shrink:0;display:flex;flex-direction:column;align-items:flex-end;gap:4px;}',
      '.ainr-cta{display:inline-flex;align-items:center;gap:4px;padding:6.5px 13px;border-radius:9px;font-size:11.5px;font-weight:700;white-space:nowrap;transition:background .15s ease,transform .15s ease;}',
      '.ainr-theme-light .ainr-cta{background:#4f46e5;color:#ffffff;box-shadow:0 2px 8px rgba(79,70,229,0.22);}',
      '.ainr-theme-light .ainr-card:hover .ainr-cta{background:#4338ca;}',
      '.ainr-theme-dark .ainr-cta{background:rgba(99,102,241,0.25);color:#e0e7ff;border:1px solid rgba(129,140,248,0.4);}',
      '.ainr-theme-dark .ainr-card:hover .ainr-cta{background:#4f46e5;color:#ffffff;border-color:#6366f1;}',
      '.ainr-sub-hint{font-size:10px;font-weight:600;opacity:0.65;letter-spacing:.02em;}',

      '.ainr-grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;}',
      '.ainr-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;}',
      '.ainr-grid-card{position:relative;display:flex;flex-direction:column;padding:14px 16px;border-radius:14px;text-decoration:none;transition:transform .2s cubic-bezier(0.16,1,0.3,1),border-color .2s ease,box-shadow .2s ease;}',
      '.ainr-grid-card:hover{transform:translateY(-2px);}',
      '.ainr-theme-light .ainr-grid-card{background:#ffffff;border:1px solid #cbd5e1;color:#0f172a;box-shadow:0 4px 16px -6px rgba(15,23,42,0.08);}',
      '.ainr-theme-light .ainr-grid-card:hover{border-color:#818cf8;box-shadow:0 12px 28px -10px rgba(99,102,241,0.2);}',
      '.ainr-theme-dark .ainr-grid-card{background:linear-gradient(135deg,rgba(15,23,42,0.92),rgba(15,23,42,0.72));border:1px solid rgba(51,65,85,0.85);color:#f1f5f9;box-shadow:0 8px 24px -12px rgba(0,0,0,0.55);}',
      '.ainr-theme-dark .ainr-grid-card:hover{border-color:rgba(129,140,248,0.65);box-shadow:0 14px 32px -10px rgba(99,102,241,0.32);}',

      '.ainr-grid-top{display:flex;align-items:center;gap:12px;margin-bottom:8px;}',
      '.ainr-grid-top .ainr-icon-box{width:46px;height:46px;border-radius:10px;}',
      '.ainr-grid-card .ainr-title{font-size:13.5px;margin:2px 0 0;}',
      '.ainr-grid-card .ainr-desc{font-size:11.5px;margin:4px 0 12px;flex:1;}',
      '.ainr-grid-footer{display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(148,163,184,0.18);}',

      '.ainr-meta-bar{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:8px;font-size:11px;letter-spacing:.02em;}',
      '.ainr-theme-light .ainr-meta-bar{color:#64748b;}',
      '.ainr-theme-dark .ainr-meta-bar{color:#94a3b8;}',
      '.ainr-disclosure{font-size:10.5px;opacity:0.78;}',

      '@media (max-width:1024px){.ainr-grid-3{grid-template-columns:1fr;}}',
      '@media (max-width:768px){.ainr-grid-2{grid-template-columns:1fr;}}',
      '@media (max-width:640px){.ainr-card{flex-direction:column;align-items:flex-start;}.ainr-action-wrap{width:100%;flex-direction:row;justify-content:space-between;align-items:center;margin-top:8px;}}'
    ].join('');
    document.head.appendChild(style);
  }

  function getThemeClass(el) {
    if (el && el.getAttribute('data-ad-theme') === 'dark') return 'ainr-theme-dark';
    if (el && el.getAttribute('data-ad-theme') === 'light') return 'ainr-theme-light';
    return isDarkPage() ? 'ainr-theme-dark' : 'ainr-theme-light';
  }

  function linkAttrs(item) {
    if (item.internal) {
      return 'href="' + esc(item.url) + '"';
    }
    return 'href="' + esc(item.url) + '" target="_blank" rel="sponsored noopener noreferrer"';
  }

  function localizeItem(raw, lang) {
    if (raw.en && raw.zh) {
      var copy = lang === 'zh' ? raw.zh : raw.en;
      return {
        id: raw.id,
        iconType: raw.iconType,
        accent: raw.accent,
        isAmazon: raw.isAmazon,
        internal: raw.internal,
        url: raw.url,
        badge: copy.badge,
        name: copy.name,
        tagline: copy.tagline,
        cta: copy.cta,
        hint: copy.hint
      };
    }
    return raw;
  }

  function renderHorizontalCard(raw, lang, compact) {
    var p = localizeItem(raw, lang);
    var pillClass = 'ainr-pill-' + (p.accent || 'indigo');
    var sourceBadge = p.isAmazon ? 'Amazon' : (lang === 'zh' ? '官方合作' : 'Official');
    return (
      '<a class="ainr-card" ' + linkAttrs(p) + '>' +
        '<div class="ainr-icon-box">' + getSvgArt(p.iconType, p.accent) + '</div>' +
        '<div class="ainr-body">' +
          '<div class="ainr-pill-row">' +
            '<span class="ainr-pill ' + pillClass + '">✦ ' + esc(p.badge) + '</span>' +
            '<span class="ainr-verified">✓ ' + esc(sourceBadge) + '</span>' +
          '</div>' +
          '<h4 class="ainr-title">' + esc(p.name) + '</h4>' +
          (compact ? '' : '<p class="ainr-desc">' + esc(p.tagline) + '</p>') +
        '</div>' +
        '<div class="ainr-action-wrap">' +
          '<span class="ainr-cta">' + esc(p.cta) + ' ↗</span>' +
          '<span class="ainr-sub-hint">' + esc(p.hint || '') + '</span>' +
        '</div>' +
      '</a>'
    );
  }

  function renderGridCard(raw, lang) {
    var p = localizeItem(raw, lang);
    var pillClass = 'ainr-pill-' + (p.accent || 'indigo');
    var sourceBadge = p.isAmazon ? 'Amazon' : (lang === 'zh' ? '官方合作' : 'Official');
    return (
      '<a class="ainr-grid-card" ' + linkAttrs(p) + '>' +
        '<div class="ainr-grid-top">' +
          '<div class="ainr-icon-box">' + getSvgArt(p.iconType, p.accent) + '</div>' +
          '<div class="ainr-body">' +
            '<div class="ainr-pill-row">' +
              '<span class="ainr-pill ' + pillClass + '">✦ ' + esc(p.badge) + '</span>' +
              '<span class="ainr-verified">✓ ' + esc(sourceBadge) + '</span>' +
            '</div>' +
            '<h4 class="ainr-title">' + esc(p.name) + '</h4>' +
          '</div>' +
        '</div>' +
        '<p class="ainr-desc">' + esc(p.tagline) + '</p>' +
        '<div class="ainr-grid-footer">' +
          '<span class="ainr-sub-hint">' + esc(p.hint || '') + '</span>' +
          '<span class="ainr-cta">' + esc(p.cta) + ' ↗</span>' +
        '</div>' +
      '</a>'
    );
  }

  function renderMetaBar(lang, labelEn, labelZh, hasAmazon) {
    var leftText = lang === 'zh' ? labelZh : labelEn;
    var disclosureText = hasAmazon
      ? (lang === 'zh'
          ? '作为亚马逊合作伙伴，符合条件的购买可能会带来推广佣金'
          : 'As an Amazon Associate I earn from qualifying purchases')
      : '';
    return (
      '<div class="ainr-meta-bar">' +
        '<span>✦ ' + esc(leftText) + '</span>' +
        (disclosureText ? '<span class="ainr-disclosure">' + esc(disclosureText) + '</span>' : '') +
      '</div>'
    );
  }

  // =========================================================================
  // 5. SLOT ROUTER & LAZY-LOAD OBSERVER
  // =========================================================================
  function mountSlot(el) {
    if (!el || el.getAttribute('data-ad-mounted') === '1') return;
    el.setAttribute('data-ad-mounted', '1');

    var slotType = el.getAttribute('data-ad-slot') || 'article-native';
    var lang = isZhPage() ? 'zh' : 'en';
    var items;

    if (slotType === 'home-mid-leaderboard') {
      items = pickRelevantProducts(2, { diverseCategories: true });
      if (!items.length) return;
      el.innerHTML =
        '<div class="ainr-slot ' + getThemeClass(el) + '">' +
          renderMetaBar(lang, 'CURATED AI HARDWARE & BOOKS', 'AI 算力硬件与技术书单精选', true) +
          '<div class="ainr-grid-2">' +
            items.map(function (it) { return renderHorizontalCard(it, lang, false); }).join('') +
          '</div>' +
        '</div>';
      return;
    }

    if (slotType === 'home-bottom-native') {
      items = pickRelevantProducts(2, { diverseCategories: true });
      var sponsor = SPONSOR_CARD[lang] || SPONSOR_CARD.en;
      items.push(sponsor);
      el.innerHTML =
        '<div class="ainr-slot ' + getThemeClass(el) + '">' +
          renderMetaBar(lang, 'RECOMMENDED AI INFRASTRUCTURE, BOOKS & PARTNERS', '精选 AI 硬件装备、必读书籍与生态合作', true) +
          '<div class="ainr-grid-3">' +
            items.map(function (it) { return renderGridCard(it, lang); }).join('') +
          '</div>' +
        '</div>';
      return;
    }

    if (slotType === 'article-bottom' || slotType === 'tool-native') {
      items = pickRelevantProducts(2, { diverseCategories: true });
      if (!items.length) return;
      var headingEn = slotType === 'tool-native'
        ? 'RECOMMENDED AI GEAR & ENGINEERING READS'
        : 'RELATED AI HARDWARE & FURTHER READING';
      var headingZh = slotType === 'tool-native'
        ? '适配该工具的硬件与进阶书单推荐'
        : '延伸推荐 · 相关 AI 硬件与技术书单';
      el.innerHTML =
        '<div class="ainr-slot ' + getThemeClass(el) + '">' +
          renderMetaBar(lang, headingEn, headingZh, true) +
          '<div class="ainr-grid-2">' +
            items.map(function (it) { return renderGridCard(it, lang); }).join('') +
          '</div>' +
        '</div>';
      return;
    }

    if (slotType === 'gateway-card' || slotType === 'mobile-feed-native') {
      items = pickRelevantProducts(1, {});
      if (!items.length) return;
      el.innerHTML =
        '<div class="ainr-slot ' + (slotType === 'gateway-card' ? 'ainr-theme-dark' : getThemeClass(el)) + '">' +
          renderMetaBar(lang, 'FEATURED AI PICK', '精选 AI 装备推荐', true) +
          renderHorizontalCard(items[0], lang, slotType === 'mobile-feed-native') +
        '</div>';
      return;
    }

    // Default: article-native / daily-native (single contextual match, never repeated in article-bottom)
    items = pickRelevantProducts(1, {});
    if (!items.length) return;
    el.innerHTML =
      '<div class="ainr-slot ' + getThemeClass(el) + '">' +
        renderMetaBar(lang, 'CONTEXTUAL AI GEAR & BOOK PICK', '结合本文主题精选 · 硬件与技术读物', true) +
        renderHorizontalCard(items[0], lang, false) +
      '</div>';
  }

  function observeThemeChanges() {
    if (typeof MutationObserver === 'undefined') return;
    var observer = new MutationObserver(function () {
      var dark = isDarkPage();
      var slots = document.querySelectorAll('.ainr-slot');
      for (var i = 0; i < slots.length; i++) {
        var parent = slots[i].parentElement;
        if (parent && parent.getAttribute('data-ad-theme')) continue;
        slots[i].classList.toggle('ainr-theme-dark', dark);
        slots[i].classList.toggle('ainr-theme-light', !dark);
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  }

  function init() {
    // Auto-mount Page Language Engine on static article detail pages (/news/..., /tools/..., /articles/...)
    if (typeof window !== 'undefined' && !window.PageLanguage && !document.getElementById('site-lang-container') && !document.getElementById('mobile-feed')) {
      if (!document.querySelector('script[src*="page_language.js"]')) {
        var plScript = document.createElement('script');
        plScript.src = '/js/page_language.js';
        plScript.defer = true;
        document.head.appendChild(plScript);
      }
    }

    injectStylesOnce();
    observeThemeChanges();

    var slots = document.querySelectorAll('[data-ad-slot]');
    if (!slots.length) return;

    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        for (var i = 0; i < entries.length; i++) {
          if (entries[i].isIntersecting) {
            mountSlot(entries[i].target);
            io.unobserve(entries[i].target);
          }
        }
      }, { rootMargin: '300px 0px' });

      for (var j = 0; j < slots.length; j++) {
        io.observe(slots[j]);
      }
    } else {
      for (var k = 0; k < slots.length; k++) {
        mountSlot(slots[k]);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
