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
  Modal,
  Spin,
  Typography,
  Divider
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
  const [selectedKey, setSelectedKey] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});
  const [stockData, setStockData] = useState([]);
  const [searchResults, setSearchResults] = useState(null);

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

  // 页面加载时获取数据
  useEffect(() => {
    fetchStats();
    fetchStockData();
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
        <Col span={6}>
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
      default:
        return renderDashboard();
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={250} theme="light">
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
            金融数据系统
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
    </Layout>
  );
};

export default App;