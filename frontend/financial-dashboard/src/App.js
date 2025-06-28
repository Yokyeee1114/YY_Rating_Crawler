// src/App.js - 主应用组件
import React, { useState, useEffect } from 'react';
import {
  Layout,
  Menu,
  Card,
  Statistic,
  Row,
  Col,
  Button,
  Table,
  Input,
  Space,
  Tag,
  message,
  Spin,
  Typography,
  Divider,
  Modal,
  Form,
  //Select,
  //Switch,
  //Tabs,
  //Collapse
} from 'antd';
import {
  DashboardOutlined,
  StockOutlined,
  FileTextOutlined,
  NotificationOutlined,
  SearchOutlined,
  SyncOutlined,
  BarChartOutlined,
  SettingOutlined
} from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';
import 'antd/dist/reset.css';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Search } = Input;
const { Title, Text } = Typography;

// 配置API基础URL
const API_BASE_URL = 'http://localhost:8000';

// 配置axios
axios.defaults.baseURL = API_BASE_URL;

const App = () => {
  // 配置模板
  const CONFIG_TEMPLATES = {
    stock_data: {
      name: "股票数据模板",
      description: "用于爬取股票价格和基本信息",
      config: {
        spider_settings: {
          download_delay: 1,
          user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        start_urls: ["https://example.com/stocks"],
        data_fields: {
          symbol: { selector: ".symbol::text", type: "string", required: true },
          name: { selector: ".name::text", type: "string", required: true },
          price: { selector: ".price::text", type: "float", required: true }
        },
        output_settings: { data_type: "stock_data" }
      }
    },
    news_data: {
      name: "新闻数据模板",
      description: "用于爬取财经新闻内容",
      config: {
        spider_settings: {
          download_delay: 2,
          user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        start_urls: ["https://example.com/news"],
        data_fields: {
          title: { selector: "h1::text", type: "string", required: true },
          content: { selector: ".content::text", type: "string", required: true },
          author: { selector: ".author::text", type: "string", required: false }
        },
        output_settings: { data_type: "financial_news" }
      }
    }
  };

  const [selectedKey, setSelectedKey] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});
  const [stockData, setStockData] = useState([]);
  const [searchResults, setSearchResults] = useState(null);
  //
  const [configs, setConfigs] = useState([]);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  // 表单相关state
  const [configForm] = Form.useForm();
  const [configModalMode, setConfigModalMode] = useState('create'); // 'create' 或 'edit'

  // 获取系统统计数据
  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/stats');
      setStats(response.data);
    } catch (error) {
      message.error('获取统计数据失败');
      console.error('Stats error:', error);
    }
  };

  // 获取股票数据
  const fetchStockData = async (limit = 20) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/stocks?limit=${limit}`);
      setStockData(response.data);
    } catch (error) {
      message.error('获取股票数据失败');
      console.error('Stock data error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 启动爬虫
  const startCrawler = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/crawl/start?spider_name=sina_stock');
      message.success(`爬虫已启动: ${response.data.message}`);
      
      // 延迟刷新数据
      setTimeout(() => {
        fetchStats();
        fetchStockData();
      }, 3000);
    } catch (error) {
      message.error('启动爬虫失败');
      console.error('Crawler error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 搜索功能
  const handleSearch = async (value) => {
    if (!value.trim()) {
      setSearchResults(null);
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`/api/search?q=${encodeURIComponent(value)}`);
      setSearchResults(response.data);
      message.success(`找到 ${response.data.stocks.length} 条相关股票数据`);
    } catch (error) {
      message.error('搜索失败');
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };
  // 自定义爬取规则功能
  // 获取配置列表
  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/configs');
      setConfigs(response.data);
    } catch (error) {
      message.error('获取配置失败');
      console.error('Config error:', error);
    } finally {
      setLoading(false);
    }
  };

// 创建配置
const createConfig = async (configData) => {
  try {
    const response = await axios.post('/api/configs', configData);
    message.success('配置创建成功');
    fetchConfigs(); // 刷新列表
    setShowConfigModal(false);
    return response.data;
  } catch (error) {
    message.error('创建配置失败');
    console.error('Create config error:', error);
  }
};
// 打开新建配置Modal
const handleCreateConfig = () => {
  setConfigModalMode('create');
  setEditingConfig(null);
  configForm.resetFields();
  setShowConfigModal(true);
};

// 应用模板
const applyTemplate = (templateKey) => {
  const template = CONFIG_TEMPLATES[templateKey];
  configForm.setFieldsValue({
    name: template.name,
    description: template.description,
    website_name: "请填写目标网站",
    config_json: JSON.stringify(template.config, null, 2)
  });
};

// 提交配置表单
const handleConfigSubmit = async (values) => {
  try {
    // 验证JSON格式
    JSON.parse(values.config_json);

    await createConfig(values);
  } catch (error) {
    if (error instanceof SyntaxError) {
      message.error('配置JSON格式错误，请检查语法');
    } else {
      message.error('保存配置失败');
    }
  }
};
// 运行配置
const handleRunConfig = async (configId) => {
  setLoading(true);
  try {
    const response = await axios.post(`/api/configs/${configId}/run`);
    message.success(`${response.data.message}`);

    // 延迟刷新数据
    setTimeout(() => {
      fetchConfigs();
      fetchStats();
      fetchStockData();
    }, 3000);
  } catch (error) {
    message.error('运行配置失败');
    console.error('Run config error:', error);
  } finally {
    setLoading(false);
  }
};

// 编辑配置（暂时占位）
const handleEditConfig = (config) => {
  message.info('编辑功能开发中...');
};

// 恢复到原始的删除配置功能（占位函数）
const handleDeleteConfig = (configId) => {
  message.info('删除功能开发中...');
};

// 页面加载时获取数据
useEffect(() => {
  fetchStats();
  fetchStockData();
  fetchConfigs(); // 获取规则
}, []);

// 股票数据表格列配置
const stockColumns = [
  {
    title: '股票代码',
    dataIndex: 'symbol',
    key: 'symbol',
    width: 120,
    render: (text) => <Text strong>{text}</Text>
  },
  {
    title: '股票名称',
    dataIndex: 'name',
    key: 'name',
    width: 150,
    render: (text) => <Text>{text}</Text>
  },
  {
    title: '当前价',
    dataIndex: 'price',
    key: 'price',
    width: 100,
    align: 'right',
    render: (text) => <Text strong style={{ fontSize: '16px' }}>¥{text}</Text>
  },
  {
    title: '涨跌额',
    dataIndex: 'change',
    key: 'change',
    width: 100,
    align: 'right',
    render: (text) => {
      const isPositive = text && text.startsWith('+');
      const isNegative = text && text.startsWith('-');
      return (
        <Text 
          style={{ 
            color: isPositive ? '#f50' : isNegative ? '#52c41a' : '#666',
            fontWeight: 'bold'
          }}
        >
          {text}
        </Text>
      );
    }
  },
  {
    title: '涨跌幅',
    dataIndex: 'change_percent',
    key: 'change_percent',
    width: 100,
    align: 'right',
    render: (text) => {
      const isPositive = text && text.startsWith('+');
      const isNegative = text && text.startsWith('-');
      return (
        <Tag color={isPositive ? 'red' : isNegative ? 'green' : 'default'}>
          {text}
        </Tag>
      );
    }
  },
  {
    title: '成交量',
    dataIndex: 'volume',
    key: 'volume',
    width: 120,
    align: 'right',
    render: (text) => {
      const volume = parseInt(text);
      if (volume > 100000000) {
        return `${(volume / 100000000).toFixed(2)}亿`;
      } else if (volume > 10000) {
        return `${(volume / 10000).toFixed(2)}万`;
      }
      return text;
    }
  },
  {
    title: '更新时间',
    dataIndex: 'crawl_time',
    key: 'crawl_time',
    width: 150,
    render: (text) => moment(text).format('MM-DD HH:mm')
  }
];

// 菜单项配置
const menuItems = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: '数据概览'
  },
  {
    key: 'stocks',
    icon: <StockOutlined />,
    label: '股票数据'
  },
  {
    key: 'reports',
    icon: <FileTextOutlined />,
    label: '研究报告'
  },
  {
    key: 'news',
    icon: <NotificationOutlined />,
    label: '财经新闻'
  },
  {
    key: 'analytics',
    icon: <BarChartOutlined />,
    label: '数据分析'
  },
    // 爬虫配置
  {
    key: 'configs',
    icon: <SettingOutlined />,
    label: '爬虫配置'
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '系统设置'
  }
];

// 渲染仪表板
const renderDashboard = () => (
  <div>
    <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
      <Col span={6}>
        <Card>
          <Statistic
            title="股票数据"
            value={stats.total_stocks || 0}
            prefix={<StockOutlined />}
            valueStyle={{ color: '#3f8600' }}
          />
        </Card>
      </Col>
      <Col span={6}>k
        <Card>
          <Statistic
            title="研究报告"
            value={stats.total_reports || 0}
            prefix={<FileTextOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="财经新闻"
            value={stats.total_news || 0}
            prefix={<NotificationOutlined />}
            valueStyle={{ color: '#722ed1' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="最后更新"
            value={stats.last_update ? moment(stats.last_update).fromNow() : '无数据'}
            valueStyle={{ color: '#666' }}
          />
        </Card>
      </Col>
    </Row>

    <Row gutter={[24, 24]}>
      <Col span={24}>
        <Card 
          title="快速操作" 
          extra={
            <Space>
              <Button 
                type="primary" 
                icon={<SyncOutlined />}
                loading={loading}
                onClick={startCrawler}
              >
                启动数据爬取
              </Button>
              <Button 
                onClick={() => {
                  fetchStats();
                  fetchStockData();
                }}
                icon={<SyncOutlined />}
              >
                刷新数据
              </Button>
            </Space>
          }
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <Search
              placeholder="搜索股票、报告或新闻..."
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              onSearch={handleSearch}
              loading={loading}
            />
            
            {searchResults && (
              <div>
                <Divider>搜索结果</Divider>
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Card size="small" title={`股票 (${searchResults.stocks.length})`}>
                      {searchResults.stocks.slice(0, 5).map(stock => (
                        <div key={stock.id} style={{ marginBottom: 8 }}>
                          <Text strong>{stock.symbol}</Text> - {stock.name}
                        </div>
                      ))}
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" title={`报告 (${searchResults.reports.length})`}>
                      {searchResults.reports.slice(0, 5).map(report => (
                        <div key={report.id} style={{ marginBottom: 8 }}>
                          <Text ellipsis>{report.title}</Text>
                        </div>
                      ))}
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" title={`新闻 (${searchResults.news.length})`}>
                      {searchResults.news.slice(0, 5).map(news => (
                        <div key={news.id} style={{ marginBottom: 8 }}>
                          <Text ellipsis>{news.title}</Text>
                        </div>
                      ))}
                    </Card>
                  </Col>
                </Row>
              </div>
            )}
          </Space>
        </Card>
      </Col>
    </Row>
  </div>
);

// 渲染股票数据页面
const renderStocks = () => (
  <Card 
    title="股票数据" 
    extra={
      <Space>
        <Button 
          type="primary" 
          icon={<SyncOutlined />}
          onClick={() => fetchStockData()}
          loading={loading}
        >
          刷新数据
        </Button>
      </Space>
    }
  >
    <Table
      columns={stockColumns}
      dataSource={stockData}
      rowKey="id"
      loading={loading}
      pagination={{
        total: stockData.length,
        pageSize: 10,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total) => `共 ${total} 条数据`
      }}
      scroll={{ x: 800 }}
    />
  </Card>
);

// 渲染其他页面的占位符
const renderPlaceholder = (title) => (
  <Card title={title}>
    <div style={{ textAlign: 'center', padding: '50px 0' }}>
      <Text type="secondary">该功能正在开发中...</Text>
    </div>
  </Card>
);
// 恢复到原始的配置页面渲染函数
const renderConfigs = () => (
  <Card
    title="爬虫配置管理"
    extra={
      <Button
        type="primary"
        onClick={handleCreateConfig}
      >
        新建配置
      </Button>
    }
  >
    <Table
      columns={[
        {
          title: '配置名称',
          dataIndex: 'name',
          key: 'name',
          render: (text) => <Text strong>{text}</Text>
        },
        {
          title: '目标网站',
          dataIndex: 'website_name',
          key: 'website_name'
        },
        {
          title: '状态',
          dataIndex: 'is_active',
          key: 'is_active',
          render: (active) => (
            <Tag color={active ? 'green' : 'red'}>
              {active ? '启用' : '禁用'}
            </Tag>
          )
        },
        {
          title: '运行次数',
          dataIndex: 'run_count',
          key: 'run_count'
        },
        {
          title: '成功次数',
          dataIndex: 'success_count',
          key: 'success_count'
        },
        {
          title: '创建时间',
          dataIndex: 'created_at',
          key: 'created_at',
          render: (text) => moment(text).format('MM-DD HH:mm')
        },
        // 恢复到原始的操作列
        {
          title: '操作',
          key: 'actions',
          width: 200,
          render: (_, record) => (
            <Space>
              <Button
                type="primary"
                size="small"
                onClick={() => handleRunConfig(record.id)}
                loading={loading}
                disabled={!record.is_active}
              >
                运行
              </Button>
              <Button
                size="small"
                onClick={() => handleEditConfig(record)}
              >
                编辑
              </Button>
              <Button
                size="small"
                danger
                onClick={() => handleDeleteConfig(record.id)}
              >
                删除
              </Button>
            </Space>
          )
        }
      ]}
      dataSource={configs}
      rowKey="id"
      loading={loading}
      pagination={{
        pageSize: 15,
        showTotal: (total) => `共 ${total} 条配置`
      }}
    />
  </Card>
);
// 渲染配置Modal
const renderConfigModal = () => (
  <Modal
    title={configModalMode === 'create' ? '新建爬虫配置' : '编辑爬虫配置'}
    open={showConfigModal}
    onCancel={() => setShowConfigModal(false)}
    width={800}
    footer={null}
  >
    <Form
      form={configForm}
      layout="vertical"
      onFinish={handleConfigSubmit}
    >
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="name"
            label="配置名称"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input placeholder="输入配置名称" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="website_name"
            label="目标网站"
            rules={[{ required: true, message: '请输入目标网站名称' }]}
          >
            <Input placeholder="例如: 新浪财经" />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        name="description"
        label="配置描述"
      >
        <Input.TextArea rows={2} placeholder="描述这个配置的用途" />
      </Form.Item>

      <Divider>配置模板</Divider>
      <Space style={{ marginBottom: 16 }}>
        <Button onClick={() => applyTemplate('stock_data')}>
          应用股票模板
        </Button>
        <Button onClick={() => applyTemplate('news_data')}>
          应用新闻模板
        </Button>
      </Space>

      <Form.Item
        name="config_json"
        label="爬虫配置 (JSON格式)"
        rules={[{ required: true, message: '请输入配置JSON' }]}
      >
        <Input.TextArea
          rows={12}
          placeholder="请输入JSON格式的爬虫配置"
          style={{ fontFamily: 'monospace' }}
        />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            保存配置
          </Button>
          <Button onClick={() => setShowConfigModal(false)}>
            取消
          </Button>
        </Space>
      </Form.Item>
    </Form>
  </Modal>
);
  // 根据选中的菜单渲染内容
  const renderContent = () => {
    switch (selectedKey) {
      case 'dashboard':
        return renderDashboard();
      case 'stocks':
        return renderStocks();
      case 'reports':
        return renderPlaceholder('研究报告');
      case 'news':
        return renderPlaceholder('财经新闻');
      case 'analytics':
        return renderPlaceholder('数据分析');
      case 'settings':
        return renderPlaceholder('系统设置');
      case 'configs':
        return renderConfigs();
      default:
        return renderDashboard();
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={250} theme="light">
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
            Scrapy数据系统
          </Title>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => setSelectedKey(key)}
          style={{ border: 'none' }}
        />
      </Sider>
      
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={3} style={{ margin: 0 }}>
                {menuItems.find(item => item.key === selectedKey)?.label || '数据概览'}
              </Title>
            </Col>
            <Col>
              <Space>
                <Text type="secondary">
                  系统状态: <Text style={{ color: '#52c41a' }}>正常运行</Text>
                </Text>
              </Space>
            </Col>
          </Row>
        </Header>
        
        <Content style={{ margin: '24px', background: '#f0f2f5' }}>
          <Spin spinning={loading}>
            {renderContent()}
          </Spin>
        </Content>
      </Layout>
      {renderConfigModal()}
    </Layout>
  );
};

export default App;